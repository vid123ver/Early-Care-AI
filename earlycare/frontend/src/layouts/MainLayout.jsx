import React from "react";
import Sidebar from "../components/Sidebar";

const MainLayout = ({ children }) => {
  return (
    <div className="app-shell medical-theme">
      <Sidebar />
      <main className="app-main">{children}</main>
    </div>
  );
};

export default MainLayout;
