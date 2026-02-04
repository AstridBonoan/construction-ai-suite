import { useEffect, useState, useRef } from "react";

export default function ProjectDelay() {
  const [projects, setProjects] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const latestRequestRef = useRef(0);

  // Prefer explicit env var (used in Docker). If missing, use relative path
  // so a Vite dev proxy can forward to the backend on localhost.
  const VITE_API_URL = import.meta.env.VITE_API_URL;
  // During development, prefer the Vite dev-server proxy (relative path).
  // In production or when VITE_API_URL is explicitly set for runtime, use that.
  const isDev = import.meta.env.DEV;
  const apiBase = VITE_API_URL ? VITE_API_URL.replace(/\/+$/, "") : "";
  const baseEndpoint = isDev ? "" : (apiBase ? apiBase : "");
  const phase9Endpoint = `${baseEndpoint}/phase9/outputs?variant=live`;
  const analyzeEndpoint = `${baseEndpoint}/api/analyze_project`;

  // Fetch projects from Phase 9 data
  useEffect(() => {
    const controller = new AbortController();
    const timeoutMs = 20000;
    const reqId = latestRequestRef.current + 1;
    latestRequestRef.current = reqId;

    const fetchProjects = async () => {
      if (latestRequestRef.current !== reqId) return;
      setLoading(true);
      setError("");
      console.log("[ProjectDelay] Fetching projects from:", phase9Endpoint);

      const timeout = setTimeout(() => {
        controller.abort();
      }, timeoutMs);

      try {
        const res = await fetch(phase9Endpoint, {
          method: "GET",
          signal: controller.signal,
          headers: { "Content-Type": "application/json" },
        });

        clearTimeout(timeout);
        console.log("[ProjectDelay] HTTP status:", res.status);

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`Backend error ${res.status} ${text}`);
        }

        const data = await res.json();
        console.log("[ProjectDelay] Projects loaded:", data?.length || 0);

        if (latestRequestRef.current === reqId) {
          const projectList = Array.isArray(data) ? data.slice(0, 10) : [];
          setProjects(projectList);
          if (projectList.length > 0) {
            setSelectedProject(projectList[0]);
          }
          setError("");
        }
      } catch (err) {
        if (err.name === "AbortError") {
          console.debug("[ProjectDelay] Request aborted");
        } else {
          console.error("[ProjectDelay] Fetch error:", err);
          if (latestRequestRef.current === reqId) {
            setError("Could not load projects — " + (err.message || "unknown error"));
          }
        }
      } finally {
        if (latestRequestRef.current === reqId) {
          setLoading(false);
        }
      }
    };

    fetchProjects();

    return () => {
      latestRequestRef.current += 1;
      controller.abort();
    };
  }, [phase9Endpoint]);

  // Analyze selected project
  const analyzeProject = async () => {
    if (!selectedProject) return;

    setAnalyzing(true);
    setAnalysis(null);
    setError("");

    try {
      const payload = {
        project_id: selectedProject.project_id || "PROJ_001",
        project_name: selectedProject.project_name || "Unknown",
        risk_score: selectedProject.risk_score || 0.5,
        delay_probability: selectedProject.delay_probability || 0.3,
        predicted_delay_days: selectedProject.predicted_delay_days || 10,
        budget: selectedProject.budget || 1000000,
        complexity: selectedProject.complexity || "medium",
      };

      console.log("[ProjectDelay] Analyzing project:", payload);

      const res = await fetch(analyzeEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Analysis failed: ${res.status} ${text}`);
      }

      const result = await res.json();
      console.log("[ProjectDelay] Analysis result:", result);
      setAnalysis(result);
    } catch (err) {
      console.error("[ProjectDelay] Analysis error:", err);
      setError("Analysis failed: " + (err.message || "unknown error"));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>🏗️ Construction AI Suite - Project Analysis</h1>
      
      {error && (
        <div style={{ color: "red", padding: "10px", backgroundColor: "#ffe6e6", borderRadius: "4px", marginBottom: "20px" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <p>📊 Loading projects from AI system...</p>
      ) : (
        <>
          <div style={{ marginBottom: "30px" }}>
            <h2>Select a Project</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "15px" }}>
              {projects.length === 0 ? (
                <p>No projects found</p>
              ) : (
                projects.map((proj, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedProject(proj)}
                    style={{
                      padding: "15px",
                      border: selectedProject?.project_name === proj.project_name ? "3px solid #2563eb" : "1px solid #ccc",
                      borderRadius: "8px",
                      cursor: "pointer",
                      backgroundColor: selectedProject?.project_name === proj.project_name ? "#eff6ff" : "#f9fafb",
                      transition: "all 0.2s",
                    }}
                  >
                    <h3 style={{ margin: "0 0 10px 0", color: "#1f2937" }}>{proj.project_name}</h3>
                    <div style={{ fontSize: "14px", color: "#666" }}>
                      <p style={{ margin: "5px 0" }}>
                        <strong>Risk Score:</strong> {(proj.risk_score * 100).toFixed(0)}%
                      </p>
                      <p style={{ margin: "5px 0" }}>
                        <strong>Delay Probability:</strong> {(proj.delay_probability * 100).toFixed(0)}%
                      </p>
                      <p style={{ margin: "5px 0" }}>
                        <strong>Est. Delay:</strong> {proj.predicted_delay_days} days
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {selectedProject && (
            <>
              <div style={{ marginBottom: "30px", padding: "20px", backgroundColor: "#f0f9ff", borderRadius: "8px", border: "1px solid #bfdbfe" }}>
                <h2>Selected Project</h2>
                <p><strong>Name:</strong> {selectedProject.project_name}</p>
                <p><strong>Risk Score:</strong> {(selectedProject.risk_score * 100).toFixed(0)}%</p>
                <p><strong>Delay Probability:</strong> {(selectedProject.delay_probability * 100).toFixed(0)}%</p>
                <p><strong>Predicted Delay:</strong> {selectedProject.predicted_delay_days} days</p>
                
                <button
                  onClick={analyzeProject}
                  disabled={analyzing}
                  style={{
                    padding: "10px 20px",
                    fontSize: "16px",
                    backgroundColor: analyzing ? "#9ca3af" : "#2563eb",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: analyzing ? "not-allowed" : "pointer",
                    marginTop: "10px",
                  }}
                >
                  {analyzing ? "⏳ Analyzing..." : "📈 AI Analysis"}
                </button>
              </div>

              {analysis && (
                <div style={{ padding: "20px", backgroundColor: "#f0fdf4", borderRadius: "8px", border: "1px solid #bbf7d0" }}>
                  <h2>✨ AI Analysis Results</h2>
                  
                  <div style={{ marginBottom: "20px" }}>
                    <h3>Risk Assessment</h3>
                    <p style={{ fontSize: "16px", lineHeight: "1.6" }}>{analysis.summary}</p>
                  </div>

                  {analysis.risk_factors && analysis.risk_factors.length > 0 && (
                    <div style={{ marginBottom: "20px", padding: "15px", backgroundColor: "#fff8dc", borderRadius: "6px", borderLeft: "4px solid #f59e0b" }}>
                      <h3 style={{ marginTop: 0, color: "#d97706" }}>Based on These Risk Factors:</h3>
                      <ul style={{ fontSize: "15px", lineHeight: "1.8", marginBottom: 0 }}>
                        {analysis.risk_factors.map((factor, idx) => (
                          <li key={idx} style={{ marginBottom: "8px" }}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis.recommendations && analysis.recommendations.length > 0 && (
                    <div style={{ marginBottom: "20px" }}>
                      <h3>Recommended Actions:</h3>
                      <ul style={{ fontSize: "15px", lineHeight: "1.8" }}>
                        {analysis.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis.delay_summary && (
                    <div style={{ marginBottom: "20px", padding: "15px", backgroundColor: "#fef3c7", borderRadius: "6px" }}>
                      <h3 style={{ marginTop: 0, color: "#b45309" }}>Delay Prediction</h3>
                      <p style={{ fontSize: "15px", lineHeight: "1.6", margin: 0 }}>{analysis.delay_summary}</p>
                    </div>
                  )}

                  {analysis.confidence && (
                    <div style={{ padding: "10px", backgroundColor: "#e0f2fe", borderRadius: "4px", marginBottom: "15px" }}>
                      <p style={{ margin: 0 }}>
                        <strong>Risk Assessment Confidence:</strong> {analysis.confidence.level} ({analysis.confidence.percentage})
                      </p>
                    </div>
                  )}

                  {analysis.delay_confidence && (
                    <div style={{ padding: "10px", backgroundColor: "#e0f2fe", borderRadius: "4px" }}>
                      <p style={{ margin: 0 }}>
                        <strong>Delay Prediction Confidence:</strong> {analysis.delay_confidence.level} ({analysis.delay_confidence.percentage})
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
