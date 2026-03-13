import asyncio
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SowRequestSerializer
from .services import SizingService, OpenAIService, DIAGRAMS_AVAILABLE

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

from asgiref.sync import async_to_sync

def run_async(coro):
    """Run an async coroutine from a sync Django view safely."""
    return async_to_sync(lambda: coro)()


# ────────────────────────────────────────────────────────────
# Views
# ────────────────────────────────────────────────────────────

class GenerateSowView(APIView):
    """
    POST /api/generate-sow/
    Accepts network-sizing parameters, returns sizing data, BOM, and an AI-generated SOW.
    """

    def post(self, request):
        serializer = SowRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 1. Calculate sizing (synchronous)
        sizing = SizingService.calculate_sizing(data)

        # 2. Build BOM + generate SOW text (both async)
        async def _gather():
            bom = await SizingService.calculate_bom(data, sizing)
            sow_text = await OpenAIService.generate_sow_content(sizing)
            return bom, sow_text

        bom, sow_text = run_async(_gather())

        return Response(
            {
                "sizing": sizing,
                "bom": bom,
                "sow_text": sow_text,
            },
            status=status.HTTP_200_OK,
        )


class GenerateDiagramView(APIView):
    """
    POST /api/generate-diagram/
    Generates a network topology diagram PNG and returns its URL.
    """

    def post(self, request):
        if not DIAGRAMS_AVAILABLE:
            return Response(
                {"detail": "Diagrams library is not installed on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            from .services import (
                Diagram, Cluster, Edge,
                Router, Switch, Firewall, Internet,
            )

            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = "network_topology"
            output_path = os.path.join(output_dir, output_filename)

            with Diagram(
                "Multi-Site Network Topology",
                show=False,
                filename=output_path,
                direction="TB",
            ):
                internet = Internet("Internet")

                with Cluster("Core Network"):
                    core_router = Router("7200VXR\n10.80.1.0/30")

                internet >> Edge(label="10.80.1.6/30") >> core_router

                with Cluster("EMEA-DUBAI 10.50.0.0/16"):
                    dubai_router = Router("7200VXR1")
                    dubai_switch = Switch("Switch11")
                    dubai_access = Switch("AccessCX1")
                    dubai_router >> Edge(label="Gi0/0") >> dubai_switch
                    dubai_switch >> Edge(label="Gi0/1") >> dubai_access

                with Cluster("US-PTB 10.61.0.0/16"):
                    ptb_router = Router("7200VXR5")
                    ptb_switch = Switch("Switch10")
                    ptb_extreme = Switch("ExtremeOs16")
                    ptb_router >> Edge(label="Gi0/0") >> ptb_switch
                    ptb_switch >> Edge(label="Mgmt") >> ptb_extreme

                with Cluster("DC-SGP 10.70.0.0/16"):
                    sgp_switch = Switch("Switch8")
                    sgp_firewall = Firewall("Fortinet")
                    sgp_switch >> Edge(label="Gi0/1") >> sgp_firewall

                with Cluster("EMEA-NL 10.51.0.0/16"):
                    nl_router = Router("7200VXR1")
                    nl_switch = Switch("Switch9")
                    nl_extreme1 = Switch("ExtremeOs15")
                    nl_access = Switch("AccessCX13")
                    nl_router >> Edge(label="Gi0/0") >> nl_switch
                    nl_switch >> Edge(label="Gi0/1") >> nl_extreme1
                    nl_switch >> Edge(label="Gi0/2") >> nl_access

                with Cluster("US-HOU 10.60.0.0/16"):
                    hou_router = Router("7200VXR3")
                    hou_extreme = Switch("ExtremeOs")
                    hou_router >> Edge(label="Mgmt") >> hou_extreme

                core_router >> Edge(label="10.80.1.12/30") >> dubai_router
                core_router >> Edge(label="10.80.1.4/30") >> ptb_router
                core_router >> Edge(label="Fa0/0") >> sgp_switch
                core_router >> Edge(label="10.80.1.0/30") >> nl_router
                core_router >> Edge(label="10.80.1.8/30") >> hou_router

            image_url = f"/static/{output_filename}.png"
            return Response({"image_url": image_url}, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response(
                {"detail": "Graphviz (dot) not found. Please install Graphviz and add it to PATH."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HealthCheckView(APIView):
    """GET /api/  — Simple health-check endpoint."""

    def get(self, request):
        return Response(
            {"message": "Network SOM/SOW Generator API is running."},
            status=status.HTTP_200_OK,
        )
