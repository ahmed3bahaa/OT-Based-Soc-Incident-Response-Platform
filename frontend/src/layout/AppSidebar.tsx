"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType, SVGProps } from "react";
import React from "react";

import { useSidebar } from "../context/SidebarContext";
import {
  BoxCubeIcon,
  DocsIcon,
  GridIcon,
  ListIcon,
  TableIcon,
} from "../icons/index";
import SidebarWidget from "./SidebarWidget";

type NavItem = {
  name: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  path: string;
};

const navItems: NavItem[] = [
  {
    icon: GridIcon,
    name: "Command",
    path: "/",
  },
  {
    icon: ListIcon,
    name: "Cases",
    path: "/cases",
  },
  {
    icon: DocsIcon,
    name: "Rules",
    path: "/rules",
  },
  {
    icon: TableIcon,
    name: "Tags",
    path: "/tags",
  },
  {
    icon: BoxCubeIcon,
    name: "Assets",
    path: "/assets",
  },
];

const AppSidebar: React.FC = () => {
  const { isExpanded, isMobileOpen, isHovered, setIsHovered } = useSidebar();
  const pathname = usePathname();
  const showText = isExpanded || isHovered || isMobileOpen;

  const isActive = (path: string) => {
    if (path === "/") {
      return pathname === "/";
    }
    return pathname === path || pathname.startsWith(`${path}/`);
  };

  return (
    <aside
      className={`fixed left-0 top-0 z-50 mt-16 flex h-screen flex-col border-r border-white/10 bg-[#080808] px-4 text-white transition-all duration-300 ease-in-out lg:mt-0 ${
        showText ? "w-[290px]" : "w-[90px]"
      } ${isMobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`flex py-7 ${showText ? "justify-start" : "justify-center"}`}>
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center border border-[#ff5a2f]/45 bg-[#ff5a2f]/12 text-sm font-bold text-[#ff5a2f] [font-family:var(--font-command)]">
            OT
          </span>
          {showText ? (
            <span>
              <span className="block text-sm uppercase text-white [font-family:var(--font-command)]">
                SOC Console
              </span>
              <span className="block text-xs text-white/38">OPC UA MVP</span>
            </span>
          ) : null}
        </Link>
      </div>

      <div className="flex flex-col overflow-y-auto duration-300 ease-linear no-scrollbar">
        <nav className="mb-6">
          <h2
            className={`mb-4 flex text-xs uppercase leading-5 text-white/34 [font-family:var(--font-command)] ${
              showText ? "justify-start" : "justify-center"
            }`}
          >
            {showText ? "Operations" : "//"}
          </h2>
          <ul className="flex flex-col gap-2">
            {navItems.map((nav) => {
              const active = isActive(nav.path);
              const Icon = nav.icon;

              return (
                <li key={nav.name}>
                  <Link
                    href={nav.path}
                    className={`group flex min-h-11 items-center gap-3 border px-3 text-sm font-medium transition [font-family:var(--font-command)] ${
                      active
                        ? "border-[#ff5a2f]/45 bg-[#ff5a2f]/12 text-[#ff5a2f]"
                        : "border-transparent text-white/55 hover:border-white/10 hover:bg-white/[0.035] hover:text-white"
                    } ${showText ? "justify-start" : "justify-center"}`}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    {showText ? <span>{nav.name}</span> : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        {showText ? <SidebarWidget /> : null}
      </div>
    </aside>
  );
};

export default AppSidebar;
