import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ProjectDelay from "./components/ProjectDelay/ProjectDelay";
import AuthLogin from "./components/saas/AuthLogin";
import Dashboard from "./components/saas/Dashboard";
import ConfigUI from "./components/saas/ConfigUI";
import Insights from "./components/saas/Insights";
import OrgManagement from "./components/saas/OrgManagement";

function App() {
  return (
    <BrowserRouter>
      <nav style={{padding:12, borderBottom:'1px solid #eee'}}>
        <Link to="/">Home</Link> | <Link to="/saas/login">Sign in</Link> | <Link to="/saas/dashboard">Dashboard</Link> | <Link to="/saas/config">Config</Link> | <Link to="/saas/insights">Insights</Link> | <Link to="/saas/org">Org</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ProjectDelay />} />
        <Route path="/saas/login" element={<AuthLogin />} />
        <Route path="/saas/dashboard" element={<Dashboard />} />
        <Route path="/saas/config" element={<ConfigUI />} />
        <Route path="/saas/insights" element={<Insights />} />
        <Route path="/saas/org" element={<OrgManagement />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
