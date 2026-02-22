import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Design from "@/pages/Design";
import Constraints from "@/pages/Constraints";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/design" element={<Design />} />
        <Route path="/constraints" element={<Constraints />} />
      </Routes>
    </Router>
  );
}
