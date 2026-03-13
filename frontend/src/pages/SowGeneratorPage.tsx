import React, { useState, ChangeEvent, FormEvent } from 'react';
import axios from 'axios';

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
    if (!data) return null;

    const { bom, sizing } = data;
    const subTotal = bom.reduce((sum: number, item: BomItem) => sum + item.total_price, 0);
    const discountRate = sizing.discount_percentage || 0;
    const discountAmount = subTotal * (discountRate / 100);
    const finalTotal = subTotal - discountAmount;
    const currency = sizing.currency || "USD";

    const downloadCSV = () => {
        const headers = ["Location,Vendor,Category,Item,Model,Description,Quantity,Unit Price,Total Price,Currency"];
        const rows = bom.map((item: BomItem) =>
            `"${item.location || ''}","${item.remarks ? (item.remarks.includes('Aruba') ? 'Aruba' : (item.remarks.includes('Cisco') ? 'Cisco' : '')) : ''}","${item.category}","${item.device_type}","${item.model}","${item.description}",${item.quantity},${item.unit_price},${item.total_price},"${item.currency}"`
        );
        // Append summary rows
        const summary = [
            `"", "", "", "", "", "Subtotal", "", "", ${subTotal}, "${currency}"`,
            `"", "", "", "", "", "Discount (${discountRate}%)", "", "", -${discountAmount}, "${currency}"`,
            `"", "", "", "", "", "Final Total", "", "", ${finalTotal}, "${currency}"`
        ];
        const csvContent = [headers, ...rows, ...summary].join("\n");
        const element = document.createElement("a");
        const file = new Blob([csvContent], { type: 'text/csv' });
        element.href = URL.createObjectURL(file);
        // Clean filename from location
        const filenameLoc = sizing.location ? sizing.location.replace(/[^a-z0-9]/gi, '_').toLowerCase() : 'predicted';
        element.download = `${filenameLoc}_BOM.csv`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    return (
        <div className="output-view" style={{ marginTop: '3rem' }}>

            {/* Sizing Summary */}
            <div style={{ marginBottom: '2rem', padding: '1.5rem', background: '#e2e3e5', borderRadius: '8px' }}>
                <h3>Predicted Sizing for {sizing.location || 'Site'}</h3>
                <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', listStyle: 'none', padding: 0 }}>
                    <li><strong>Total Ports Needed:</strong> {sizing.total_ports_needed}</li>
                    <li><strong>Switches Required:</strong> {sizing.switches_required_48_port}</li>
                    <li><strong>PoE Ports:</strong> {sizing.poe_ports_required}</li>
                    <li><strong>Uplinks:</strong> {sizing.uplinks_required}</li>
                </ul>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2>Final Bill of Materials ({currency})</h2>
                <button onClick={downloadCSV} style={{ padding: '0.5rem 1rem', background: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                    Download CSV
                </button>
            </div>

            <div style={{ background: 'white', padding: '1rem', borderRadius: '4px', border: '1px solid #dee2e6' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ background: '#343a40', color: 'white' }}>
                        <tr>
                            <th style={{ padding: '0.75rem', textAlign: 'left' }}>Location</th>
                            <th style={{ padding: '0.75rem', textAlign: 'left' }}>Category</th>
                            <th style={{ padding: '0.75rem', textAlign: 'left' }}>Item</th>
                            <th style={{ padding: '0.75rem', textAlign: 'left' }}>Model</th>
                            <th style={{ padding: '0.75rem', textAlign: 'left' }}>Description</th>
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
                                <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{item.model}</td>
                                <td style={{ padding: '0.75rem' }}>{item.description}</td>
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
    );
};

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
// MAIN PAGE COMPONENT
// ==========================================

const SowGeneratorPage: React.FC = () => {
    const [result, setResult] = useState<GenerateSowResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

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

    return (
        <div className="page-container">
            <h1>Bill Of Materials Generator</h1>
            <p>Enter your office requirements below.</p>

            <div className="card" style={{ background: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <RequirementForm onGenerate={handleGenerate} loading={loading} />
                {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}
            </div>

            {result && <OutputView data={result} />}
        </div>
    );
};

export default SowGeneratorPage;
