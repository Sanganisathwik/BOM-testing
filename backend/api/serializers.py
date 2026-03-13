from rest_framework import serializers


class SowRequestSerializer(serializers.Serializer):
    vendor = serializers.ChoiceField(choices=["Aruba", "Cisco"], default="Aruba")
    location = serializers.CharField(max_length=100, default="HQ-01")
    currency = serializers.ChoiceField(
        choices=["USD", "INR", "EUR", "GBP", "AUD", "CAD"], default="USD"
    )
    users = serializers.IntegerField(min_value=0)
    wifi_aps = serializers.IntegerField(min_value=0)
    iot_devices = serializers.IntegerField(min_value=0)
    other_devices = serializers.IntegerField(min_value=0, default=0)
    firewalls = serializers.IntegerField(min_value=0, default=0)
    connectivity = serializers.CharField(max_length=100, default="10GB Fiber")
    redundancy = serializers.BooleanField(default=True)
    discount_percentage = serializers.FloatField(min_value=0.0, max_value=100.0, default=0.0)


class SowResponseSerializer(serializers.Serializer):
    sizing = serializers.DictField()
    sow_text = serializers.CharField()
    bom = serializers.ListField(child=serializers.DictField())
