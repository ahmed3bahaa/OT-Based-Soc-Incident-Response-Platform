import { useSidebar } from "@/context/SidebarContext";
import React from "react";

const Backdrop: React.FC = () => {
  const { isMobileOpen, toggleMobileSidebar } = useSidebar();

  if (!isMobileOpen) return null;

  return (
    <div
      className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm lg:hidden"
      onClick={toggleMobileSidebar}
    />
  );
};

export default Backdrop;
