import React, { useState, ChangeEvent, FormEvent } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// ==========================================
// TYPES & INTERFACES
// ==========================================

interface SizingData {
    location?: string;
    total_ports_needed: number;
    switches_required_48_port: number;
    poe_ports_required: number;
    uplinks_required: number;
    discount_percentage?: number;
    currency?: string;
}

interface BomItem {
    location: string;
    category: string;
    device_type: string;
    model: string;
    description: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    currency: string;
    remarks?: string;
    image_url?: string;
}

interface GenerateSowResponse {
    sizing: SizingData;
    bom: BomItem[];
    sow_text: string;
}

interface FormData {
    vendor: string;
    location: string;
    currency: string;
    users: number;
    wifi_aps: number;
    iot_devices: number;
    firewalls: number;
    connectivity: string;
    redundancy: boolean;
    discount_percentage?: number;
}

interface RequirementFormProps {
    onGenerate: (data: FormData) => void;
    loading: boolean;
}

interface OutputViewProps {
    data: GenerateSowResponse;
}

// ==========================================
// SUB-COMPONENTS
// ==========================================

const RequirementForm: React.FC<RequirementFormProps> = ({ onGenerate, loading }) => {
    const [formData, setFormData] = useState<FormData>({
        vendor: 'Aruba',
        location: '',
        currency: 'USD',
        users: 100,
        wifi_aps: 10,
        iot_devices: 20,
        firewalls: 1,
        connectivity: '10GB Fiber',
        redundancy: true
    });

    const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        const checked = (e.target as HTMLInputElement).checked;

        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        onGenerate(formData);
    };

    return (
        <div className="selection-panel" style={{ padding: '2rem', border: '1px solid #e9ecef', borderRadius: '8px', background: '#f8f9fa' }}>
            <h3 style={{ marginTop: 0, color: '#495057', marginBottom: '1.5rem' }}>Project Requirements</h3>
            <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>

                {/* Vendor - New Field */}
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Preferred Vendor</label>
                    <select
                        name="vendor"
                        value={formData.vendor}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    >
                        <option value="Aruba">Aruba (HPE)</option>
                        <option value="Cisco">Cisco Systems</option>
                    </select>
                </div>

                {/* Location - New Field */}
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Location (Site Name)</label>
                    <input
                        type="text"
                        name="location"
                        placeholder="e.g. New York HQ"
                        value={formData.location}
                        onChange={handleChange}
                        required
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                {/* Currency - New Field */}
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Currency</label>
                    <select
                        name="currency"
                        value={formData.currency}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    >
                        <option value="USD">USD ($)</option>
                        <option value="INR">INR (₹)</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Number of Users</label>
                    <input
                        type="number"
                        name="users"
                        min="0"
                        value={formData.users}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>WiFi Access Points</label>
                    <input
                        type="number"
                        name="wifi_aps"
                        min="0"
                        value={formData.wifi_aps}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>IoT Devices</label>
                    <input
                        type="number"
                        name="iot_devices"
                        min="0"
                        value={formData.iot_devices}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Firewalls Required</label>
                    <input
                        type="number"
                        name="firewalls"
                        min="0"
                        value={formData.firewalls}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Uplink Connectivity</label>
                    <select
                        name="connectivity"
                        value={formData.connectivity}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    >
                        <option value="1GB Copper">1GB Copper</option>
                        <option value="10GB Fiber">10GB Fiber</option>
                        <option value="MPLS">MPLS</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Discount Rate (%)</label>
                    <input
                        type="number"
                        name="discount_percentage"
                        min="0"
                        max="100"
                        step="0.1"
                        value={formData.discount_percentage || 0}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da' }}
                    />
                </div>

                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <input
                        type="checkbox"
                        name="redundancy"
                        checked={formData.redundancy}
                        onChange={handleChange}
                        id="redundancy"
                        style={{ width: '20px', height: '20px', marginRight: '10px' }}
                    />
                    <label htmlFor="redundancy" style={{ fontWeight: 'bold', cursor: 'pointer' }}>High Availability (Redundancy)</label>
                </div>

                <div style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                    <button
                        type="submit"
                        disabled={loading}
                        style={{ width: '100%', padding: '1rem', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1.1rem', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}
                    >
                        {loading ? 'Generating...' : 'Predict Requirements & Generate BOM'}
                    </button>
                </div>
            </form>
        </div>
    );
};

const OutputView: React.FC<OutputViewProps> = ({ data }) => {
    const [viewTab, setViewTab] = useState<'bom' | 'sow'>('sow');

    if (!data) return null;

    const { bom, sizing, sow_text } = data;
    const subTotal = bom.reduce((sum: number, item: BomItem) => sum + item.total_price, 0);
    const discountRate = sizing.discount_percentage || 0;
    const discountAmount = subTotal * (discountRate / 100);
    const finalTotal = subTotal - discountAmount;
    const currency = sizing.currency || "USD";

    const downloadCSV = () => {
        const headers = ["Location,Vendor,Category,Item,Model,Description,Quantity,Unit Price,Total Price,Currency"];
        const rows = bom.map((item: BomItem) =>
            `"${item.location || ''}","${item.remarks || ''}","${item.category}","${item.device_type}","${item.model}","${item.description}",${item.quantity},${item.unit_price},${item.total_price},"${item.currency}"`
        );
        const summary = [
            `"", "", "", "", "", "Subtotal", "", "", ${subTotal}, "${currency}"`,
            `"", "", "", "", "", "Discount (${discountRate}%)", "", "", -${discountAmount}, "${currency}"`,
            `"", "", "", "", "", "Final Total", "", "", ${finalTotal}, "${currency}"`
        ];
        const csvContent = [headers, ...rows, ...summary].join("\n");
        const element = document.createElement("a");
        const file = new Blob([csvContent], { type: 'text/csv' });
        element.href = URL.createObjectURL(file);
        const filenameLoc = sizing.location ? sizing.location.replace(/[^a-z0-9]/gi, '_').toLowerCase() : 'predicted';
        element.download = `${filenameLoc}_BOM.csv`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    const downloadHLD = () => {
        const element = document.createElement("a");
        const file = new Blob([sow_text], { type: 'text/markdown' });
        element.href = URL.createObjectURL(file);
        const filenameLoc = sizing.location ? sizing.location.replace(/[^a-z0-9]/gi, '_').toLowerCase() : 'predicted';
        element.download = `${filenameLoc}_HLD.md`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    const downloadDocx = async () => {
        try {
            const response = await axios.post('http://localhost:8000/api/export-docx/', 
                { markdown: sow_text }, 
                { responseType: 'blob' }
            );
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            const filenameLoc = sizing.location ? sizing.location.replace(/[^a-z0-9]/gi, '_').toLowerCase() : 'predicted';
            link.setAttribute('download', `${filenameLoc}_HLD.docx`);
            document.body.appendChild(link);
            link.click();
            if (link.parentNode) link.parentNode.removeChild(link);
        } catch (error) {
            console.error("Failed to download DOCX", error);
            alert("Failed to generate Word document.");
        }
    };

    return (
        <div className="output-view" style={{ marginTop: '3rem' }}>
            
            {/* View Switching Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '2px solid #e9ecef', paddingBottom: '0.5rem' }}>
                <button 
                    onClick={() => setViewTab('sow')} 
                    style={{ padding: '0.7rem 1.5rem', background: viewTab === 'sow' ? '#17a2b8' : 'transparent', color: viewTab === 'sow' ? 'white' : '#495057', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    📄 High-Level Design (HLD)
                </button>
                <button 
                    onClick={() => setViewTab('bom')} 
                    style={{ padding: '0.7rem 1.5rem', background: viewTab === 'bom' ? '#007bff' : 'transparent', color: viewTab === 'bom' ? 'white' : '#495057', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    📊 Structured BOM
                </button>
            </div>

            {/* Sizing Summary Header */}
            <div style={{ marginBottom: '2rem', padding: '1.5rem', background: '#e9eef5', borderRadius: '8px', borderLeft: '4px solid #007bff' }}>
                <h3 style={{ marginTop: 0, color: '#0056b3' }}>Derived Sizing for {sizing.location || 'Site'}</h3>
                <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', listStyle: 'none', padding: 0 }}>
                    <li><strong>Total Ports Needed:</strong> {sizing.total_ports_needed}</li>
                    <li><strong>Switches Required:</strong> {sizing.switches_required_48_port}</li>
                    <li><strong>PoE Ports Available/Required:</strong> {sizing.poe_ports_required}</li>
                    <li><strong>Uplink Trunks Required:</strong> {sizing.uplinks_required}</li>
                </ul>
            </div>

            {viewTab === 'bom' ? (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2>Final Bill of Materials ({currency})</h2>
                        <button onClick={downloadCSV} style={{ padding: '0.6rem 1.2rem', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                            Download CSV
                        </button>
                    </div>

                    <div style={{ background: 'white', padding: '1rem', borderRadius: '4px', border: '1px solid #dee2e6', overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead style={{ background: '#343a40', color: 'white' }}>
                                <tr>
                                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Location</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Category</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Item</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'center' }}>Image</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Model</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'center' }}>Qty</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Unit Price</th>
                                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bom.map((item: BomItem, index: number) => (
                                    <tr key={index} style={{ borderBottom: '1px solid #dee2e6' }}>
                                        <td style={{ padding: '0.75rem' }}>{item.location}</td>
                                        <td style={{ padding: '0.75rem' }}>{item.category}</td>
                                        <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#007bff' }}>{item.device_type}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                            {item.image_url ? (
                                                <img src={item.image_url} alt={item.model} style={{ width: '25px', height: '25px', objectFit: 'contain', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '4px' }} referrerPolicy="no-referrer" />
                                            ) : '-'}
                                        </td>
                                        <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{item.model}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>{item.quantity}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{item.unit_price.toLocaleString(undefined, { style: 'currency', currency: item.currency })}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 'bold' }}>{item.total_price.toLocaleString(undefined, { style: 'currency', currency: item.currency })}</td>
                                    </tr>
                                ))}
                                <tr style={{ background: '#f8f9fa' }}>
                                    <td colSpan={7} style={{ padding: '1rem', textAlign: 'right', fontWeight: 'bold' }}>Subtotal:</td>
                                    <td style={{ padding: '1rem', textAlign: 'right', fontSize: '1.1rem' }}>{subTotal.toLocaleString(undefined, { style: 'currency', currency: currency })}</td>
                                </tr>
                                {discountRate > 0 && (
                                    <tr style={{ background: '#fff3cd', color: '#856404' }}>
                                        <td colSpan={7} style={{ padding: '1rem', textAlign: 'right', fontWeight: 'bold' }}>Discount ({discountRate}%):</td>
                                        <td style={{ padding: '1rem', textAlign: 'right', fontSize: '1.1rem' }}>- {discountAmount.toLocaleString(undefined, { style: 'currency', currency: currency })}</td>
                                    </tr>
                                )}
                                <tr style={{ background: '#d4edda', fontWeight: 'bold', borderTop: '2px solid #28a745' }}>
                                    <td colSpan={7} style={{ padding: '1rem', textAlign: 'right', fontSize: '1.2rem' }}>Final Total:</td>
                                    <td style={{ padding: '1rem', textAlign: 'right', fontSize: '1.3rem', color: '#155724' }}>{finalTotal.toLocaleString(undefined, { style: 'currency', currency: currency })}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2>High-Level Design Document</h2>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={downloadHLD} style={{ padding: '0.6rem 1.2rem', background: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                                Download HLD (.md)
                            </button>
                            <button onClick={downloadDocx} style={{ padding: '0.6rem 1.2rem', background: '#0d6efd', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                                Download HLD (.docx)
                            </button>
                        </div>
                    </div>
                    <div style={{ background: '#ffffff', padding: '2rem', borderRadius: '6px', border: '1px solid #dee2e6', maxHeight: '600px', overflowY: 'auto' }}>
                        <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', color: '#2c3e50', lineHeight: 1.6, margin: 0 }}>
                            <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    h1: ({node, ...props}: any) => <h1 style={{color: '#1a365d', marginTop: '1.5rem', marginBottom: '1rem', borderBottom: '2px solid #2b6cb0', paddingBottom: '0.5rem', fontSize: '2rem'}} {...props} />,
                                    h2: ({node, ...props}: any) => <h2 style={{color: '#2b6cb0', marginTop: '1.5rem', marginBottom: '0.8rem', fontSize: '1.5rem'}} {...props} />,
                                    h3: ({node, ...props}: any) => <h3 style={{color: '#2c5282', marginTop: '1.2rem', marginBottom: '0.6rem', fontSize: '1.25rem'}} {...props} />,
                                    table: ({node, ...props}: any) => <div style={{overflowX: 'auto', margin: '1.5rem 0'}}><table style={{width: '100%', borderCollapse: 'collapse', border: '1px solid #e2e8f0'}} {...props} /></div>,
                                    thead: ({node, ...props}: any) => <thead style={{background: '#2d3748', color: '#ffffff'}} {...props} />,
                                    th: ({node, ...props}: any) => <th style={{padding: '0.75rem', textAlign: 'left', fontWeight: 'bold'}} {...props} />,
                                    td: ({node, ...props}: any) => <td style={{borderBottom: '1px solid #edf2f7', padding: '0.75rem'}} {...props} />,
                                    blockquote: ({node, ...props}: any) => <blockquote style={{borderLeft: '4px solid #3182ce', paddingLeft: '1rem', margin: '1rem 0', color: '#4a5568', fontStyle: 'italic'}} {...props} />,
                                    li: ({node, ...props}: any) => <li style={{marginBottom: '0.5rem'}} {...props} />,
                                    img: ({node, ...props}: any) => <img style={{maxWidth: '150px', height: 'auto', borderRadius: '6px', margin: '0.5rem 1rem 1rem 0', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}} {...props} />
                                }}
                            >
                                {sow_text}
                            </ReactMarkdown>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};;

// ==========================================
// HIGH LEVEL DESIGN COMPONENT
// ==========================================

const HighLevelDesign: React.FC = () => {
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const generateDiagram = async () => {
        setLoading(true);
        setError(null);
        setImageUrl(null); // Reset previous image

        try {
            // Add timestamp to avoid browser caching
            const response = await axios.post('http://localhost:8000/api/generate-diagram/');
            const path = response.data.image_url;
            setImageUrl(`http://localhost:8000${path}?t=${new Date().getTime()}`);
        } catch (err: any) {
            console.error(err);
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError("Failed to generate diagram. Ensure backend is running and Graphviz is installed.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ marginTop: '2rem', padding: '2rem', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h2 style={{ marginTop: 0 }}>High Level Design</h2>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>Generate a visual network topology diagram representing the standard architecture.</p>

            <button
                onClick={generateDiagram}
                disabled={loading}
                style={{
                    padding: '0.8rem 1.5rem',
                    background: '#6f42c1',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '1rem',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                }}
            >
                {loading ? (
                    <>
                        <span style={{ display: 'inline-block', width: '16px', height: '16px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></span>
                        Generating Diagram...
                    </>
                ) : 'Generate Network Topology'}
            </button>
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>

            {error && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#f8d7da', color: '#721c24', borderRadius: '4px', borderLeft: '4px solid #dc3545' }}>
                    <strong>Error:</strong> {error}
                </div>
            )}

            {imageUrl && (
                <div style={{ marginTop: '2rem', textAlign: 'center', background: '#f8f9fa', padding: '1rem', borderRadius: '8px', border: '1px solid #dee2e6' }}>
                    <img src={imageUrl} alt="Network Topology" style={{ maxWidth: '100%', maxHeight: '800px', height: 'auto', boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }} />
                </div>
            )}
        </div>
    );
};

// ==========================================
// CHAT INPUT COMPONENT
// ==========================================

interface ChatInputProps {
    onGenerate: (text: string) => void;
    loading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onGenerate, loading }) => {
    const [text, setText] = useState<string>("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (text.trim()) {
            onGenerate(text);
        }
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label style={{ fontWeight: 'bold', color: '#495057' }}>Describe your network requirements</label>
            <textarea
                rows={8}
                placeholder="e.g. outline the design for a office in London for 100 users, 20 APs, High Availability, Cisco..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ced4da', resize: 'vertical', fontSize: '1rem' }}
                required
            />
            <button
                type="submit"
                disabled={loading}
                style={{ padding: '1rem', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1.1rem', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}
            >
                {loading ? 'Analyzing & Generating...' : 'Generate with AI'}
            </button>
        </form>
    );
};

// ==========================================
// MAIN PAGE COMPONENT
// ==========================================

const SowGeneratorPage: React.FC = () => {
    const [result, setResult] = useState<GenerateSowResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'form' | 'chat'>('chat');

    const handleGenerate = async (formData: FormData) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post<GenerateSowResponse>('http://localhost:8000/api/generate-sow/', formData);
            setResult(response.data);
        } catch (err: any) {
            console.error(err);
            setError("Failed to generate BOM. Ensure backend is running.");
        } finally {
            setLoading(false);
        }
    };

    const handleChatGenerate = async (text: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post<GenerateSowResponse>('http://localhost:8000/api/generate-sow/chat/', { text });
            setResult(response.data);
        } catch (err: any) {
            console.error(err);
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError("Failed to generate BOM from description. Ensure backend is running and AI service is configured.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <h1>Bill Of Materials Generator</h1>
            <p style={{ color: '#666' }}>Generate a network configuration using a natural description or a manual form.</p>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <button 
                    onClick={() => setActiveTab('chat')} 
                    style={{ padding: '0.8rem 1.2rem', background: activeTab === 'chat' ? '#007bff' : '#e9ecef', color: activeTab === 'chat' ? 'white' : '#495057', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    💡 AI Chat Description
                </button>
                <button 
                    onClick={() => setActiveTab('form')} 
                    style={{ padding: '0.8rem 1.2rem', background: activeTab === 'form' ? '#007bff' : '#e9ecef', color: activeTab === 'form' ? 'white' : '#495057', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    📋 Manual Form
                </button>
            </div>

            <div className="card" style={{ background: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                {activeTab === 'chat' ? (
                    <ChatInput onGenerate={handleChatGenerate} loading={loading} />
                ) : (
                    <RequirementForm onGenerate={handleGenerate} loading={loading} />
                )}
                {error && <div style={{ color: '#721c24', background: '#f8d7da', padding: '1rem', marginTop: '1rem', borderRadius: '4px', borderLeft: '4px solid #dc3545' }}><strong>Error:</strong> {error}</div>}
            </div>

            {result && <OutputView data={result} />}
        </div>
    );
};

export default SowGeneratorPage;
