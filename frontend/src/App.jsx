import { Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import HealthChat from "./pages/HealthChat";
import ImageAnalyzer from "./pages/ImageAnalyzer";
import MedicationHistory from "./pages/MedicationHistory";
import MedicalReportHistory from "./pages/MedicalReportHistory";
import HealthRecords from "./pages/HealthRecords";
import ClinicalReview from "./pages/ClinicalReview";
import SymptomChecker from "./pages/SymptomChecker";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return <Routes><Route path="/" element={<Navigate to="/login" replace />} /><Route path="/login" element={<Login />} /><Route path="/register" element={<Register />} /><Route element={<ProtectedRoute />}><Route path="/dashboard" element={<Dashboard />} /><Route path="/health-chat" element={<HealthChat />} /><Route path="/symptom-checker" element={<SymptomChecker />} /><Route path="/medicine-scanner" element={<ImageAnalyzer />} /><Route path="/report-analyzer" element={<ImageAnalyzer />} /><Route path="/medication-history" element={<MedicationHistory />} /><Route path="/medical-reports" element={<MedicalReportHistory />} /><Route path="/health-records" element={<HealthRecords />} /><Route path="/clinical-review" element={<ClinicalReview />} /></Route><Route path="*" element={<Navigate to="/login" replace />} /></Routes>;
}
