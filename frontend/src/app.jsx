import React, { useEffect, useState, useMemo } from "react";
console.log("🔥 NEW UNI_MAT APP IS RUNNING 🔥");
const API_BASE = "http://127.0.0.1:8000/api";

function App() {
  const [registry, setRegistry] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [syncingSap, setSyncingSap] = useState(false);

  const [files, setFiles] = useState({
    alpha: null,
    beta: null,
    gamma: null,
  });

  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [remarks, setRemarks] = useState("");
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // =========================================================
  // FETCH DATA
  // =========================================================

  const fetchData = async () => {
    setLoading(true);

    try {
      const [registryResponse, metricsResponse] = await Promise.all([
        fetch(`${API_BASE}/national-registry`),
        fetch(`${API_BASE}/accuracy`),
      ]);

      const registryData = await registryResponse.json();
      const metricsData = await metricsResponse.json();

      if (registryData.status === "success") {
        setRegistry(registryData.data || []);
      }

      if (metricsData.status === "success") {
        setMetrics(metricsData);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // =========================================================
  // HELPERS
  // =========================================================

  const getNationalId = (item) =>
    item.national_material_id ||
    item.national_code ||
    "N/A";

  const getDescription = (item) =>
    item.description ||
    item.standardized_description ||
    "Material description unavailable";

  const getSpecification = (item) =>
    item.specification ||
    item.technical_specification ||
    "";

  const getCategory = (item) =>
    item.category ||
    item.material_type ||
    item.attributes?.product ||
    "Material";

  const getStatus = (item) =>
    item.governance?.status ||
    item.status ||
    "PENDING";

  const getConfidence = (item) => {
    const score =
      item.confidence ??
      item.confidence_score ??
      item.match_confidence;

    if (score === undefined || score === null || score === "") {
      return null;
    }

    return Number(score);
  };

  // =========================================================
  // DASHBOARD COUNTS
  // =========================================================

  const dashboardStats = useMemo(() => {
    const approved = registry.filter(
      (item) => getStatus(item) === "APPROVED"
    ).length;

    const declined = registry.filter(
      (item) => getStatus(item) === "DECLINED"
    ).length;

    const pending = registry.length - approved - declined;

    return {
      total: registry.length,
      approved,
      pending,
      declined,
    };
  }, [registry]);

  // =========================================================
  // SEARCH
  // =========================================================

  const filteredRegistry = useMemo(() => {
    const query = search.toLowerCase().trim();

    if (!query) return registry;

    return registry.filter((item) => {
      const id = getNationalId(item).toLowerCase();
      const description = getDescription(item).toLowerCase();
      const category = getCategory(item).toLowerCase();

      return (
        id.includes(query) ||
        description.includes(query) ||
        category.includes(query)
      );
    });
  }, [registry, search]);

  // =========================================================
  // FILE UPLOAD
  // =========================================================

  const handleFileChange = (event, cpse) => {
    const file = event.target.files?.[0] || null;

    setFiles((previous) => ({
      ...previous,
      [cpse]: file,
    }));
  };

  const handleUpload = async () => {
    if (!files.alpha || !files.beta || !files.gamma) {
      alert("Please select all three CPSE CSV files.");
      return;
    }

    setUploading(true);

    const formData = new FormData();

    formData.append("alpha_file", files.alpha);
    formData.append("beta_file", files.beta);
    formData.append("gamma_file", files.gamma);

    try {
      const response = await fetch(
        `${API_BASE}/upload-datasets`,
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "Dataset upload failed."
        );
      }

      alert(
        `Successfully processed ${
          result.records_processed || 0
        } national material records.`
      );

      setFiles({
        alpha: null,
        beta: null,
        gamma: null,
      });

      await fetchData();
    } catch (error) {
      console.error("Upload failed:", error);
      alert(error.message);
    } finally {
      setUploading(false);
    }
  };

  // =========================================================
  // SAP SYNC
  // =========================================================

  const handleSapSync = async () => {
    setSyncingSap(true);

    try {
      const response = await fetch(
        `${API_BASE}/erp/sync-sap`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "SAP synchronization failed."
        );
      }

      alert(
        result.message ||
          "SAP synchronization completed successfully."
      );

      await fetchData();
    } catch (error) {
      console.error("SAP sync failed:", error);
      alert(error.message);
    } finally {
      setSyncingSap(false);
    }
  };

  // =========================================================
  // APPROVE / DECLINE
  // =========================================================

  const updateStatus = async (nationalId, newStatus) => {
    setUpdatingStatus(true);

    try {
      const response = await fetch(
        `${API_BASE}/national-registry/${encodeURIComponent(
          nationalId
        )}/status?status=${newStatus}`,
        {
          method: "PATCH",
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "Failed to update status."
        );
      }

      setSelectedMaterial(null);
      setRemarks("");

      await fetchData();
    } catch (error) {
      console.error("Status update failed:", error);
      alert(error.message);
    } finally {
      setUpdatingStatus(false);
    }
  };

  // =========================================================
  // OPEN DETAILS
  // =========================================================

  const openDetails = (item) => {
    setSelectedMaterial(item);
    setRemarks(item.governance?.remarks || "");
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-800">

      {/* =====================================================
          SIDEBAR
      ====================================================== */}

      <aside className="fixed left-0 top-0 bottom-0 hidden lg:flex w-64 bg-[#0B1220] text-white flex-col">

        <div className="px-7 py-7 border-b border-white/10">

          <div className="flex items-center gap-3">

            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center font-black text-lg shadow-lg shadow-blue-500/20">
              U
            </div>

            <div>
              <h1 className="text-xl font-black tracking-tight">
                UNI_MAT
              </h1>

              <p className="text-[10px] text-slate-400 uppercase tracking-widest">
                Material Intelligence
              </p>
            </div>

          </div>

        </div>

        <nav className="flex-1 px-4 py-6">

          <SidebarItem
            icon="⌂"
            label="Dashboard"
            active
          />

          <SidebarItem
            icon="▣"
            label="Material Registry"
          />

          <SidebarItem
            icon="✦"
            label="AI Matching"
          />

          <SidebarItem
            icon="✓"
            label="Review Queue"
          />

          <SidebarItem
            icon="◈"
            label="Analytics"
          />

          <div className="my-6 border-t border-white/10" />

          <SidebarItem
            icon="⇧"
            label="Data Import"
          />

          <SidebarItem
            icon="↻"
            label="SAP / ERP"
          />

        </nav>

        <div className="p-5 border-t border-white/10">

          <div className="flex items-center gap-3">

            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-sm font-bold">
              A
            </div>

            <div>
              <p className="text-sm font-semibold">
                Administrator
              </p>

              <p className="text-xs text-slate-500">
                Governance
              </p>
            </div>

          </div>

        </div>

      </aside>

      {/* =====================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="lg:ml-64">

        <div className="max-w-[1600px] mx-auto px-6 md:px-10 py-7">

          {/* =================================================
              HEADER
          ================================================== */}

          <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-5 mb-8">

            <div>

              <p className="text-sm font-semibold text-blue-600 mb-1">
                NATIONAL MATERIAL INTELLIGENCE
              </p>

              <h2 className="text-3xl md:text-4xl font-black text-[#0B1220] tracking-tight">
                Material Master Dashboard
              </h2>

              <p className="text-slate-500 mt-2">
                Standardize, match and govern material records
                across CPSE systems.
              </p>

            </div>

            <div className="flex gap-3">

              <button
                onClick={fetchData}
                disabled={loading}
                className="px-4 py-2.5 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition font-semibold text-sm shadow-sm"
              >
                {loading ? "Refreshing..." : "↻ Refresh"}
              </button>

              <button
                onClick={handleSapSync}
                disabled={syncingSap}
                className="px-5 py-2.5 rounded-xl bg-[#0B1220] hover:bg-slate-800 disabled:bg-slate-400 text-white font-semibold text-sm shadow-lg"
              >
                {syncingSap
                  ? "Syncing..."
                  : "Sync SAP / ERP"}
              </button>

            </div>

          </header>

          {/* =================================================
              STAT CARDS
          ================================================== */}

          <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">

            <DashboardCard
              label="National Materials"
              value={dashboardStats.total}
              description="Total standardized records"
              icon="▣"
              gradient="from-blue-500 to-cyan-500"
            />

            <DashboardCard
              label="Pending Review"
              value={dashboardStats.pending}
              description="Require human governance"
              icon="◷"
              gradient="from-violet-500 to-purple-500"
            />

            <DashboardCard
              label="Approved"
              value={dashboardStats.approved}
              description="Governance approved"
              icon="✓"
              gradient="from-emerald-500 to-teal-500"
            />

            <DashboardCard
              label="Declined"
              value={dashboardStats.declined}
              description="Rejected mappings"
              icon="×"
              gradient="from-rose-500 to-orange-500"
            />

          </section>

          {/* =================================================
              AI STATUS BANNER
          ================================================== */}

          <section className="relative overflow-hidden rounded-2xl bg-[#0B1220] text-white p-6 md:p-7 mb-8 shadow-xl">

            <div className="absolute -right-20 -top-20 w-64 h-64 rounded-full bg-blue-500/20 blur-3xl" />

            <div className="absolute right-40 -bottom-20 w-64 h-64 rounded-full bg-violet-500/20 blur-3xl" />

            <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-5">

              <div className="flex items-start gap-4">

                <div className="w-12 h-12 rounded-xl bg-white/10 border border-white/10 flex items-center justify-center text-xl">
                  ✦
                </div>

                <div>

                  <p className="text-xs font-bold text-cyan-300 uppercase tracking-widest">
                    AI Matching Engine
                  </p>

                  <h3 className="text-xl font-bold mt-1">
                    Hybrid material intelligence is active
                  </h3>

                  <p className="text-sm text-slate-400 mt-1">
                    NLP standardization + semantic similarity +
                    structured attribute verification
                  </p>

                </div>

              </div>

              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-400/20">

                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />

                <span className="text-sm font-semibold text-emerald-300">
                  Engine Online
                </span>

              </div>

            </div>

          </section>

          {/* =================================================
              MODEL METRICS
          ================================================== */}

          {metrics && (

            <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-8">

              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-5">

                <div>

                  <h3 className="text-lg font-bold text-slate-900">
                    Model Evaluation
                  </h3>

                  <p className="text-sm text-slate-500 mt-1">
                    Benchmark performance on the evaluation dataset
                  </p>

                </div>

                <span className="px-3 py-1.5 rounded-full bg-violet-50 text-violet-700 text-xs font-bold">
                  BENCHMARK
                </span>

              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

                <MetricBox
                  label="Evaluated"
                  value={metrics.total_evaluated}
                />

                <MetricBox
                  label="Correct Matches"
                  value={metrics.correct_matches}
                />

                <MetricBox
                  label="Accuracy"
                  value={`${metrics.accuracy_percentage}%`}
                />

                <MetricBox
                  label="Precision"
                  value={`${metrics.precision_percentage}%`}
                />

              </div>

            </section>

          )}

          {/* =================================================
              DATA IMPORT
          ================================================== */}

          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-8">

            <div className="flex items-start gap-3 mb-5">

              <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                ⇧
              </div>

              <div>

                <h3 className="font-bold text-slate-900">
                  Import CPSE Material Data
                </h3>

                <p className="text-sm text-slate-500 mt-1">
                  Upload source material masters for AI
                  standardization and matching.
                </p>

              </div>

            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">

              <FileInput
                label="CPSE Alpha"
                file={files.alpha}
                onChange={(event) =>
                  handleFileChange(event, "alpha")
                }
              />

              <FileInput
                label="CPSE Beta"
                file={files.beta}
                onChange={(event) =>
                  handleFileChange(event, "beta")
                }
              />

              <FileInput
                label="CPSE Gamma"
                file={files.gamma}
                onChange={(event) =>
                  handleFileChange(event, "gamma")
                }
              />

              <button
                onClick={handleUpload}
                disabled={uploading}
                className="h-11 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 disabled:from-slate-400 disabled:to-slate-400 text-white font-bold shadow-lg shadow-blue-500/20 transition"
              >
                {uploading
                  ? "AI Processing..."
                  : "Upload & Process"}
              </button>

            </div>

          </section>

          {/* =================================================
              REGISTRY
          ================================================== */}

          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

            <div className="p-6 border-b border-slate-200">

              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">

                <div>

                  <div className="flex items-center gap-2">

                    <h3 className="text-xl font-black text-slate-900">
                      National Material Registry
                    </h3>

                    <span className="px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-bold">
                      {filteredRegistry.length}
                    </span>

                  </div>

                  <p className="text-sm text-slate-500 mt-1">
                    Unified national view of standardized materials
                  </p>

                </div>

                <div className="relative w-full lg:w-96">

                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                    ⌕
                  </span>

                  <input
                    type="text"
                    placeholder="Search material or national code..."
                    value={search}
                    onChange={(event) =>
                      setSearch(event.target.value)
                    }
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 text-sm"
                  />

                </div>

              </div>

            </div>

            <div className="overflow-x-auto">

              <table className="w-full">

                <thead>

                  <tr className="bg-slate-50 border-b border-slate-200">

                    <th className="px-6 py-4 text-left text-[11px] font-black uppercase tracking-wider text-slate-400">
                      National Material
                    </th>

                    <th className="px-6 py-4 text-left text-[11px] font-black uppercase tracking-wider text-slate-400">
                      Standardized Description
                    </th>

                    <th className="px-6 py-4 text-left text-[11px] font-black uppercase tracking-wider text-slate-400">
                      Category
                    </th>

                    <th className="px-6 py-4 text-left text-[11px] font-black uppercase tracking-wider text-slate-400">
                      AI Confidence
                    </th>

                    <th className="px-6 py-4 text-left text-[11px] font-black uppercase tracking-wider text-slate-400">
                      Status
                    </th>

                    <th className="px-6 py-4 text-right text-[11px] font-black uppercase tracking-wider text-slate-400">
                      Action
                    </th>

                  </tr>

                </thead>

                <tbody className="divide-y divide-slate-100">

                  {filteredRegistry.length === 0 ? (

                    <tr>

                      <td
                        colSpan="6"
                        className="px-6 py-16 text-center"
                      >

                        <div className="w-14 h-14 rounded-2xl bg-slate-100 mx-auto flex items-center justify-center text-2xl text-slate-400 mb-3">
                          ▣
                        </div>

                        <p className="font-bold text-slate-700">
                          No material records found
                        </p>

                        <p className="text-sm text-slate-400 mt-1">
                          Try another search or upload material data.
                        </p>

                      </td>

                    </tr>

                  ) : (

                    filteredRegistry.map((item) => {

                      const confidence = getConfidence(item);

                      return (

                        <tr
                          key={getNationalId(item)}
                          className="hover:bg-blue-50/30 transition"
                        >

                          {/* NATIONAL CODE */}

                          <td className="px-6 py-5">

                            <p className="font-black text-slate-900 text-sm">
                              {getNationalId(item)}
                            </p>

                            <p className="text-[11px] text-slate-400 mt-1">
                              National standard
                            </p>

                          </td>

                          {/* DESCRIPTION */}

                          <td className="px-6 py-5 max-w-md">

                            <p className="font-semibold text-slate-700 text-sm">
                              {getDescription(item)}
                            </p>

                            {getSpecification(item) && (

                              <p className="text-xs text-slate-400 mt-1 truncate max-w-sm">
                                {getSpecification(item)}
                              </p>

                            )}

                          </td>

                          {/* CATEGORY */}

                          <td className="px-6 py-5">

                            <span className="inline-flex px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 text-xs font-bold">
                              {getCategory(item)}
                            </span>

                          </td>

                          {/* CONFIDENCE */}

                          <td className="px-6 py-5">

                            {confidence !== null ? (

                              <ConfidenceBadge
                                score={confidence}
                              />

                            ) : (

                              <div>

                                <span className="text-slate-400 font-bold">
                                  —
                                </span>

                                <p className="text-[10px] text-slate-400 mt-1">
                                  Pending AI score
                                </p>

                              </div>

                            )}

                          </td>

                          {/* STATUS */}

                          <td className="px-6 py-5">

                            <StatusBadge
                              status={getStatus(item)}
                            />

                          </td>

                          {/* ACTION */}

                          <td className="px-6 py-5 text-right">

                            <button
                              onClick={() =>
                                openDetails(item)
                              }
                              className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
                            >
                              View Details →
                            </button>

                          </td>

                        </tr>

                      );
                    })

                  )}

                </tbody>

              </table>

            </div>

          </section>

        </div>

      </main>

      {/* =======================================================
          MATERIAL DETAILS DRAWER
      ======================================================== */}

      {selectedMaterial && (

        <div className="fixed inset-0 z-50">

          {/* BACKDROP */}

          <div
            className="absolute inset-0 bg-[#0B1220]/60 backdrop-blur-sm"
            onClick={() =>
              setSelectedMaterial(null)
            }
          />

          {/* DRAWER */}

          <div className="absolute right-0 top-0 bottom-0 w-full max-w-2xl bg-white shadow-2xl overflow-y-auto">

            {/* DRAWER HEADER */}

            <div className="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-slate-200 px-7 py-5">

              <div className="flex items-center justify-between">

                <div>

                  <p className="text-[11px] font-black uppercase tracking-widest text-violet-600">
                    AI Material Analysis
                  </p>

                  <h2 className="text-xl font-black text-slate-900 mt-1">
                    {getNationalId(selectedMaterial)}
                  </h2>

                </div>

                <button
                  onClick={() =>
                    setSelectedMaterial(null)
                  }
                  className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 text-xl"
                >
                  ×
                </button>

              </div>

            </div>

            <div className="p-7 space-y-7">

              {/* MATERIAL */}

              <div>

                <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Standardized Material
                </p>

                <h3 className="text-2xl font-black text-slate-900 mt-2">
                  {getDescription(selectedMaterial)}
                </h3>

              </div>

              {/* SCORE */}

              <div className="rounded-2xl bg-gradient-to-br from-[#0B1220] to-[#182642] p-6 text-white relative overflow-hidden">

                <div className="absolute right-0 top-0 w-40 h-40 bg-blue-500/20 blur-3xl rounded-full" />

                <div className="relative">

                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Match Confidence
                  </p>

                  {getConfidence(selectedMaterial) !== null ? (

                    <p className="text-5xl font-black mt-2">
                      {getConfidence(selectedMaterial)}%
                    </p>

                  ) : (

                    <p className="text-4xl font-black mt-2 text-slate-400">
                      —
                    </p>

                  )}

                  <div className="mt-4">

                    <StatusBadge
                      status={getStatus(selectedMaterial)}
                    />

                  </div>

                </div>

              </div>

              {/* SPECIFICATION */}

              {getSpecification(selectedMaterial) && (

                <div>

                  <SectionTitle title="Specification" />

                  <div className="mt-3 rounded-xl bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700">
                    {getSpecification(selectedMaterial)}
                  </div>

                </div>

              )}

              {/* ATTRIBUTES */}

              {selectedMaterial.attributes &&
                Object.keys(selectedMaterial.attributes).length > 0 && (

                  <div>

                    <SectionTitle title="Extracted Attributes" />

                    <div className="grid grid-cols-2 gap-3 mt-3">

                      {Object.entries(
                        selectedMaterial.attributes
                      ).map(([key, value]) => {

                        if (
                          value === null ||
                          value === undefined ||
                          value === ""
                        ) {
                          return null;
                        }

                        return (

                          <div
                            key={key}
                            className="rounded-xl border border-slate-200 p-4 bg-white"
                          >

                            <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                              {key.replaceAll("_", " ")}
                            </p>

                            <p className="font-bold text-slate-800 mt-1">
                              {String(value)}
                            </p>

                          </div>

                        );
                      })}

                    </div>

                  </div>

                )}

              {/* CPSE SOURCES */}

              <div>

                <div className="flex items-center justify-between">

                  <SectionTitle title="CPSE Source Mapping" />

                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Restricted detail
                  </span>

                </div>

                <p className="text-xs text-slate-500 mt-1 mb-3">
                  Original source codes are shown only in the
                  detailed material view.
                </p>

                <div className="space-y-3">

                  {selectedMaterial.mapped_cpse_materials?.length ? (

                    selectedMaterial.mapped_cpse_materials.map(
                      (material, index) => (

                        <div
                          key={index}
                          className="rounded-xl border border-slate-200 p-4 bg-slate-50"
                        >

                          <div className="flex items-center justify-between">

                            <div>

                              <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                                Source CPSE
                              </p>

                              <p className="font-bold text-slate-900 mt-1">
                                {material.cpse_id ||
                                  material.source ||
                                  "CPSE"}
                              </p>

                            </div>

                            <div className="text-right">

                              <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                                Original Material Code
                              </p>

                              <p className="font-mono font-black text-blue-700 mt-1">
                                {material.original_code ||
                                  "N/A"}
                              </p>

                            </div>

                          </div>

                        </div>

                      )
                    )

                  ) : (

                    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-sm text-slate-500">
                      No CPSE mappings available.
                    </div>

                  )}

                </div>

              </div>

              {/* REMARKS */}

              <div>

                <SectionTitle title="Governance Remarks" />

                <textarea
                  value={remarks}
                  onChange={(event) =>
                    setRemarks(event.target.value)
                  }
                  rows="4"
                  placeholder="Enter review justification..."
                  className="w-full mt-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 resize-none"
                />

              </div>

              {/* ACTION */}

              <div className="grid grid-cols-2 gap-3 pt-2 pb-4">

                <button
                  disabled={updatingStatus}
                  onClick={() =>
                    updateStatus(
                      getNationalId(selectedMaterial),
                      "DECLINED"
                    )
                  }
                  className="py-3.5 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 font-bold disabled:opacity-50"
                >
                  {updatingStatus
                    ? "Updating..."
                    : "✕ Decline"}
                </button>

                <button
                  disabled={updatingStatus}
                  onClick={() =>
                    updateStatus(
                      getNationalId(selectedMaterial),
                      "APPROVED"
                    )
                  }
                  className="py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold disabled:bg-slate-400 shadow-lg shadow-emerald-500/20"
                >
                  {updatingStatus
                    ? "Updating..."
                    : "✓ Approve"}
                </button>

              </div>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

// =============================================================
// SIDEBAR ITEM
// =============================================================

function SidebarItem({
  icon,
  label,
  active = false,
}) {
  return (
    <button
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-1 text-sm font-semibold transition ${
        active
          ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
          : "text-slate-400 hover:bg-white/5 hover:text-white"
      }`}
    >
      <span className="w-5 text-center">
        {icon}
      </span>

      {label}
    </button>
  );
}

// =============================================================
// DASHBOARD CARD
// =============================================================

function DashboardCard({
  label,
  value,
  description,
  icon,
  gradient,
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition">

      <div className="flex items-start justify-between">

        <div>

          <p className="text-xs font-black uppercase tracking-wider text-slate-400">
            {label}
          </p>

          <p className="text-3xl font-black text-slate-900 mt-2">
            {value}
          </p>

        </div>

        <div
          className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} text-white flex items-center justify-center text-lg shadow-lg`}
        >
          {icon}
        </div>

      </div>

      <p className="text-xs text-slate-400 mt-3">
        {description}
      </p>

    </div>
  );
}

// =============================================================
// METRIC BOX
// =============================================================

function MetricBox({ label, value }) {
  return (
    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">

      <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <p className="text-xl font-black text-slate-900 mt-1">
        {value}
      </p>

    </div>
  );
}

// =============================================================
// FILE INPUT
// =============================================================

function FileInput({
  label,
  file,
  onChange,
}) {
  return (
    <div>

      <label className="block text-xs font-black uppercase tracking-wider text-slate-500 mb-2">
        {label}
      </label>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">

        <input
          type="file"
          accept=".csv"
          onChange={onChange}
          className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 file:font-bold"
        />

        {file && (

          <p className="text-xs text-emerald-600 font-semibold mt-2 truncate">
            ✓ {file.name}
          </p>

        )}

      </div>

    </div>
  );
}

// =============================================================
// CONFIDENCE
// =============================================================

function ConfidenceBadge({ score }) {
  let label = "MEDIUM";
  let classes =
    "bg-amber-50 text-amber-700 border-amber-200";

  if (score >= 90) {
    label = "HIGH";
    classes =
      "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (score < 70) {
    label = "LOW";
    classes =
      "bg-red-50 text-red-700 border-red-200";
  }

  return (
    <div>

      <div className="flex items-center gap-2">

        <span className="font-black text-slate-800">
          {score}%
        </span>

        <span
          className={`px-2 py-0.5 rounded-full border text-[9px] font-black ${classes}`}
        >
          {label}
        </span>

      </div>

      <div className="w-24 h-1.5 bg-slate-100 rounded-full mt-2 overflow-hidden">

        <div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500"
          style={{
            width: `${Math.min(
              Math.max(score, 0),
              100
            )}%`,
          }}
        />

      </div>

    </div>
  );
}

// =============================================================
// STATUS
// =============================================================

function StatusBadge({ status }) {
  const normalized = String(
    status || "PENDING"
  ).toUpperCase();

  let classes =
    "bg-amber-50 text-amber-700 border-amber-200";

  if (normalized === "APPROVED") {
    classes =
      "bg-emerald-50 text-emerald-700 border-emerald-200";
  }

  if (normalized === "DECLINED") {
    classes =
      "bg-red-50 text-red-700 border-red-200";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border text-[10px] font-black ${classes}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {normalized}
    </span>
  );
}

// =============================================================
// SECTION TITLE
// =============================================================

function SectionTitle({ title }) {
  return (
    <h3 className="text-sm font-black text-slate-900">
      {title}
    </h3>
  );
}

export default App;