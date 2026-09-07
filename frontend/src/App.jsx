import { HashRouter, Navigate, Routes, Route } from "react-router-dom";
import Uploader from "./pages/Uploader";
import RunnerList from "./pages/RunnerList";
import RunnerDetail from "./pages/RunnerDetail";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Uploader />} />
        <Route path="/runner/:file_id" element={<RunnerList />} />
        <Route path="/runner/:file_id/:athlete/:race_id" element={<RunnerDetail />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </HashRouter>
  );
}
