import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, MiniMap, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

interface SizingProps {
    sizing: {
        firewalls: number;
        switches_required_48_port: number;
        uplinks_required: number;
        connectivity: string;
        ap_ports: number;
        users_ports: number;
        iot_ports: number;
    };
}

const NetworkTopology: React.FC<SizingProps> = ({ sizing }) => {
    // Memoize nodes and edges calculation
    const { initialNodes, initialEdges } = useMemo(() => {
        if (!sizing) return { initialNodes: [], initialEdges: [] };

        const nodes: Node[] = [];
        const edges: Edge[] = [];
        let yPos = 50;
        const centerX = 400; // Center of the canvas

        // --- 1. Internet (Top) ---
        nodes.push({
            id: 'internet',
            type: 'input', // Input type for top-level
            data: { label: 'Internet Cloud' },
            position: { x: centerX, y: yPos },
            style: {
                background: '#E3F2FD',
                color: '#0D47A1',
                border: '1px solid #2196F3',
                borderRadius: '50%',
                width: 100,
                height: 100,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontWeight: 'bold'
            },
        });
        yPos += 150;

        // --- 2. Firewall ---
        let parentId = 'internet';
        // If firewalls are required, add layer
        if (sizing.firewalls > 0) {
            nodes.push({
                id: 'firewall',
                data: { label: `Firewall Cluster\n(x${sizing.firewalls} Active/Standby)` },
                position: { x: centerX, y: yPos },
                style: {
                    background: '#FFEBEE',
                    color: '#B71C1C',
                    border: '2px solid #F44336',
                    borderRadius: '4px',
                    width: 180
                },
            });
            edges.push({ id: 'e-int-fw', source: parentId, target: 'firewall', type: 'smoothstep', animated: true });
            parentId = 'firewall';
            yPos += 150;
        }

        // --- 3. Core Switch ---
        nodes.push({
            id: 'core',
            data: { label: 'Core / Distribution Layer\n(L3 Switching)' },
            position: { x: centerX, y: yPos },
            style: {
                background: '#E8F5E9',
                color: '#1B5E20',
                border: '2px solid #4CAF50',
                width: 250,
                fontWeight: 'bold'
            },
        });
        edges.push({ id: `e-${parentId}-core`, source: parentId, target: 'core', type: 'smoothstep', animated: true });
        parentId = 'core';
        yPos += 150;

        // --- 4. Access Layer (Aggregated for visual simplicity) ---
        // We show one big node representing the stack
        nodes.push({
            id: 'access',
            data: { label: `Access Layer Stack\n(${sizing.switches_required_48_port} x 48-Port Switches)` },
            position: { x: centerX, y: yPos },
            style: {
                background: '#F1F8E9',
                border: '2px dashed #8BC34A',
                width: 220
            },
        });
        edges.push({
            id: 'e-core-access',
            source: 'core',
            target: 'access',
            type: 'smoothstep',
            label: `${sizing.uplinks_required} Uplinks (${sizing.connectivity})`,
            animated: true
        });
        parentId = 'access';
        yPos += 180;

        // --- 5. Endpoints (WiFi, IoT, Users) ---
        // We spread these out horizontally below the Access Layer

        // WiFi
        if (sizing.ap_ports > 0) {
            nodes.push({
                id: 'wifi',
                type: 'output',
                data: { label: `WiFi Coverage\n(x${sizing.ap_ports} APs)` },
                position: { x: centerX - 250, y: yPos },
                style: { background: '#FFF3E0', border: '1px solid #FF9800', width: 150 }
            });
            edges.push({ id: 'e-acc-wifi', source: 'access', target: 'wifi', type: 'default', label: 'PoE+' });
        }

        // Wired Users
        if (sizing.users_ports > 0) {
            nodes.push({
                id: 'users',
                type: 'output',
                data: { label: `Wired Users\n(x${sizing.users_ports} Connections)` },
                position: { x: centerX, y: yPos },
                style: { background: '#FAFAFA', border: '1px solid #9E9E9E', width: 150 }
            });
            edges.push({ id: 'e-acc-users', source: 'access', target: 'users', type: 'default' });
        }

        // IoT
        if (sizing.iot_ports > 0) {
            nodes.push({
                id: 'iot',
                type: 'output',
                data: { label: `IoT Devices\n(x${sizing.iot_ports} Sensors/Cams)` },
                position: { x: centerX + 250, y: yPos },
                style: { background: '#F3E5F5', border: '1px solid #9C27B0', width: 150 }
            });
            edges.push({ id: 'e-acc-iot', source: 'access', target: 'iot', type: 'default', label: 'IoT VLAN' });
        }

        return { initialNodes: nodes, initialEdges: edges };
    }, [sizing]);

    return (
        <div style={{ height: '600px', width: '100%', border: '1px solid #dee2e6', borderRadius: '8px', background: '#fff' }}>
            <ReactFlow
                nodes={initialNodes}
                edges={initialEdges}
                fitView
                attributionPosition="bottom-right"
            >
                <MiniMap nodeStrokeColor={(n: Node) => {
                    if (n.style?.background) return n.style.background as string;
                    if (n.type === 'input') return '#0041d0';
                    if (n.type === 'output') return '#ff0072';
                    if (n.type === 'default') return '#1a192b';
                    return '#eee';
                }} />
                <Controls />
                <Background color="#aaa" gap={16} />
            </ReactFlow>
        </div>
    );
};

export default NetworkTopology;
