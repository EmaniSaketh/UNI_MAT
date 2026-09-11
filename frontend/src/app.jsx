import { useState, useEffect } from 'react';

function App() {
  const [registry, setRegistry] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [uploading, setUploading] = useState(false);
  const [syncingSap, setSyncingSap] = useState(false);
  const [files, setFiles] = useState({ alpha: null, beta: null, gamma: null });

  const fetchData = async () => {
    setLoading(true);
    try {
      const metricsRes = await fetch('http://127.0.0.1:8000/api/accuracy');
      const metricsData = await metricsRes.json();
      if (metricsData.status === 'success') setMetrics(metricsData);

      const registryRes = await fetch('http://127.0.0.1:8000/api/national-registry');
      const registryData = await registryRes.json();
      if (registryData.status === 'success') setRegistry(registryData.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFileChange = (e, cpse) => {
    setFiles({ ...files, [cpse]: e.target.files[0] });
  };

  const handleUpload = async () => {
    if (!files.alpha || !files.beta || !files.gamma) {
      alert("Please select all three CPSE CSV files first!");
      return;
    }
    setUploading(true);
    
    const formData = new FormData();
    formData.append("alpha_file", files.alpha);
    formData.append("beta_file", files.beta);
    formData.append("gamma_file", files.gamma);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload-datasets', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (result.status === "success") {
        alert("Success! AI is processing the new National Codes.");
        fetchData();
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Error uploading. Is the Python backend running?");
    }
    setUploading(false);
  };

  const handleSapSync = async () => {
    setSyncingSap(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/erp/sync-sap', {
        method: 'POST',
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'SAP sync failed');
      alert(result.message);
      fetchData();
    } catch (error) {
      console.error("SAP sync failed:", error);
      alert(error.message);
    }
    setSyncingSap(false);
  };

  const updateStatus = async (nationalId, newStatus) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/national-registry/${nationalId}/status?status=${newStatus}`, {
        method: 'PATCH'
      });
      const result = await response.json();
      if (response.ok) {
        fetchData();
      } else {
        alert(result.detail || "Failed to update status");
      }
    } catch (error) {
      console.error("Status update failed:", error);
      alert("Error updating status.");
    }
  };

  const filteredRegistry = registry.filter(item => 
    item.standardized_description.toLowerCase().includes(search.toLowerCase()) ||
    item.national_material_id.toLowerCase().includes(search.toLowerCase()) ||
    item.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen p-8 bg-gray-50 text-gray-800 font-sans">
      <div className="max-w-7xl mx-auto">
        
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-blue-900">UniMat AI</h1>
            <p className="text-gray-500 mt-1">National Material Master Registry</p>
          </div>
          <div className="space-x-3">
            <button onClick={fetchData} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow">
              {loading ? 'Refreshing...' : '🔄 Refresh Data'}
            </button>
            <button onClick={handleSapSync} disabled={syncingSap} className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded shadow">
              {syncingSap ? 'Syncing SAP...' : 'Sync SAP/ERP'}
            </button>
          </div>
        </header>

        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-4 rounded shadow border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase">Total Evaluated</p>
              <p className="text-2xl font-extrabold text-gray-800">{metrics.total_evaluated}</p>
            </div>
            <div className="bg-white p-4 rounded shadow border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase">Correct Matches</p>
              <p className="text-2xl font-extrabold text-green-600">{metrics.correct_matches}</p>
            </div>
            <div className="bg-white p-4 rounded shadow border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase">Accuracy Percentage</p>
              <p className="text-2xl font-extrabold text-blue-600">{metrics.accuracy_percentage}%</p>
            </div>
            <div className="bg-white p-4 rounded shadow border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase">Precision Percentage</p>
              <p className="text-2xl font-extrabold text-indigo-600">{metrics.precision_percentage}%</p>
            </div>
          </div>
        )}

        {/* Upload Panel */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8 border border-blue-100">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Upload New CPSE Inventory (CSV)</h2>
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-xs font-bold text-gray-600 uppercase mb-1">CPSE Alpha</label>
              <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'alpha')} className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-bold text-gray-600 uppercase mb-1">CPSE Beta</label>
              <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'beta')} className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700" />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-bold text-gray-600 uppercase mb-1">CPSE Gamma</label>
              <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'gamma')} className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700" />
            </div>
            <button onClick={handleUpload} disabled={uploading} className={`py-2 px-6 rounded font-bold text-white shadow ${uploading ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'}`}>
              {uploading ? 'Processing AI...' : 'Upload & Process'}
            </button>
          </div>
        </div>

        {/* Search & Table */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <input type="text" placeholder="Search by National ID or description..." className="w-full p-3 mb-6 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500" value={search} onChange={(e) => setSearch(e.target.value)} />
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider border-b">
                  <th className="p-4 font-semibold">National ID</th>
                  <th className="p-4 font-semibold">Standardized Description</th>
                  <th className="p-4 font-semibold">Category</th>
                  <th className="p-4 font-semibold">Legacy Codes</th>
                  <th className="p-4 font-semibold">Status</th>
                  <th className="p-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredRegistry.length === 0 ? (
                  <tr><td colSpan="6" className="p-8 text-center text-red-500 font-bold">No records found. Please upload datasets above.</td></tr>
                ) : (
                  filteredRegistry.map((item) => {
                    const currentStatus = item.governance?.status || item.status || 'PENDING';
                    return (
                      <tr key={item.national_material_id} className="hover:bg-gray-50">
                        <td className="p-4 font-bold text-gray-800">{item.national_material_id}</td>
                        <td className="p-4 uppercase text-sm text-gray-700">{item.standardized_description}</td>
                        <td className="p-4"><span className="bg-blue-50 text-blue-700 text-xs font-bold px-2 py-1 rounded">{item.category}</span></td>
                        <td className="p-4 space-y-1">
                          {item.mapped_cpse_materials.map((m, idx) => (
                            <div key={idx} className="text-xs bg-gray-100 p-1.5 rounded border border-gray-200">
                              <b>{m.cpse_id}:</b> {m.original_code}
                            </div>
                          ))}
                        </td>
                        <td className="p-4">
                          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                            currentStatus === 'APPROVED' ? 'bg-green-100 text-green-800' :
                            currentStatus === 'DECLINED' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {currentStatus}
                          </span>
                        </td>
                        <td className="p-4 text-right space-x-2 whitespace-nowrap">
                          <button 
                            onClick={() => updateStatus(item.national_material_id, 'APPROVED')}
                            className="bg-green-50 hover:bg-green-100 text-green-700 font-semibold text-xs px-3 py-1.5 rounded border border-green-200 shadow-sm"
                          >
                            Approve
                          </button>
                          <button 
                            onClick={() => updateStatus(item.national_material_id, 'DECLINED')}
                            className="bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs px-3 py-1.5 rounded border border-red-200 shadow-sm"
                          >
                            Decline
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;