import React from "react";
import { METRO_COLORS, METRO_GSC_LOGO_DATA_URL } from "../assets/metroBrand";
import type { User } from "../types/talentflow";

export type ActiveTab = "dashboard" | "requests" | "committee" | "workforce" | "audit" | "admin";

export function formatINR(value: string | number | undefined): string {
  const num = Number(value ?? 0);
  if (Number.isNaN(num)) return "₹0.00";
  if (num >= 10_000_000) {
    return `₹${(num / 10_000_000).toFixed(2)} Cr`;
  }
  if (num >= 100_000) {
    return `₹${(num / 100_000).toFixed(2)} L`;
  }
  return `₹${num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    APPROVED: { bg: "#dcfce7", fg: "#166534" },
    RECRUITING: { bg: "#dcf1ff", fg: "#003B7E" },
    PARTIALLY_FILLED: { bg: "#dcf1ff", fg: "#003B7E" },
    FILLED: { bg: "#d1fae5", fg: "#065f46" },
    COMMITTEE_PENDING: { bg: "#f9ae00", fg: "#000000" },
    FINANCE_REVIEW: { bg: "rgba(0, 59, 126, 0.12)", fg: "#003B7E" },
    MANAGER_REVIEW: { bg: "rgba(0, 137, 203, 0.15)", fg: "#003B7E" },
    CLARIFICATION_REQUESTED: { bg: "#ffedd5", fg: "#9a3412" },
    REJECTED: { bg: "#fee2e2", fg: "#991b1b" },
    CANCELLED: { bg: "#f3f4f6", fg: "#4b5563" },
    DRAFT: { bg: "#f1f5f9", fg: "#323232" },
  };
  const style = colors[status] || { bg: "#f1f5f9", fg: "#323232" };
  return (
    <span
      style={{
        background: style.bg,
        color: style.fg,
        padding: "4px 10px",
        borderRadius: "6px",
        fontSize: "12px",
        fontWeight: 800,
      }}
    >
      {status}
    </span>
  );
}

export function KpiCard({
  title,
  value,
  subtitle,
  highlight,
}: {
  title: string;
  value: string;
  subtitle: string;
  highlight?: string;
}) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #d1d1d1",
        borderTop: `4px solid ${highlight ?? METRO_COLORS.primaryNavy}`,
        borderRadius: "10px",
        padding: "18px 20px",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 59, 126, 0.05)",
      }}
    >
      <div style={{ fontSize: "13px", color: "#4f4f4f", fontWeight: 700 }}>{title}</div>
      <div
        style={{
          fontSize: "26px",
          fontWeight: 800,
          fontFamily: "'Manrope', sans-serif",
          color: highlight ?? METRO_COLORS.primaryNavy,
          margin: "8px 0 4px",
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: "12px", color: "#4f4f4f", fontWeight: 600 }}>{subtitle}</div>
    </div>
  );
}

export function MetroHeader({
  users,
  currentUserId,
  onUserChange,
  onPopulateDemoQueue,
}: {
  users: User[];
  currentUserId: string;
  onUserChange: (newId: string) => void;
  onPopulateDemoQueue: () => void;
}) {
  return (
    <header
      className="metro-glass-header"
      style={{
        background:
          "linear-gradient(99.79deg, rgba(255, 255, 255, 0.95) 1.95%, rgba(255, 255, 255, 0.84) 96.47%)",
        backdropFilter: "blur(20px) saturate(180%)",
        color: METRO_COLORS.primaryNavy,
        padding: "14px 28px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: "3px solid #f9ae00",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 59, 126, 0.08)",
        flexWrap: "wrap",
        gap: "16px",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "18px", flexWrap: "wrap" }}>
        <a
          href="https://www.metro-gsc.in/"
          target="_blank"
          rel="noreferrer"
          style={{ display: "flex", alignItems: "center", textDecoration: "none" }}
        >
          <img
            src={METRO_GSC_LOGO_DATA_URL}
            alt="METRO Global Solution Center"
            style={{ height: "42px", width: "auto", display: "block" }}
          />
        </a>
        <div style={{ borderLeft: "2px solid rgba(0, 59, 126, 0.2)", paddingLeft: "18px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "21px",
              fontWeight: 800,
              fontFamily: "'Manrope', sans-serif",
              color: METRO_COLORS.primaryNavy,
              letterSpacing: "-0.01em",
            }}
          >
            <span style={{ color: METRO_COLORS.tertiaryCyan }}>Talent</span>
            <span style={{ color: METRO_COLORS.secondaryGold }}>Flow</span>{" "}
            <span style={{ fontWeight: 700, fontSize: "17px", color: METRO_COLORS.primaryNavy }}>
              — Hiring &amp; People Committee Platform
            </span>
          </h1>
          <div style={{ fontSize: "12px", color: "#4f4f4f", marginTop: "2px", fontWeight: 600 }}>
            <span>TalentFlow — Enterprise Hiring &amp; People Committee Platform</span> • METRO Global Solution Center • Cloud SQL PostgreSQL + BigQuery Warehouse (
            <code style={{ color: METRO_COLORS.primaryNavy }}>talentflow_analytics</code>) • RBAC &amp; SoD Enforced
          </div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={onPopulateDemoQueue}
          style={{
            padding: "8px 14px",
            borderRadius: "8px",
            border: "1px solid #0089cb",
            background: "#0089cb",
            color: "#ffffff",
            fontWeight: 700,
            fontSize: "12px",
            cursor: "pointer",
            boxShadow: "0 2px 5px 0 rgba(0,0,0,0.16)",
          }}
        >
          + Populate / Restore Approval Queue
        </button>
        <label
          htmlFor="role-switcher"
          style={{ fontSize: "13px", color: METRO_COLORS.primaryNavy, fontWeight: 700 }}
        >
          Acting Role:
        </label>
        <select
          id="role-switcher"
          aria-label="Acting Role"
          value={currentUserId}
          onChange={(e) => onUserChange(e.target.value)}
          style={{
            padding: "7px 12px",
            borderRadius: "8px",
            border: "2px solid #003B7E",
            background: "#ffffff",
            color: "#003B7E",
            fontWeight: 700,
          }}
        >
          {users.length === 0 ? (
            <option value="usr-committee">Priya Menon (COMMITTEE_MEMBER)</option>
          ) : (
            users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name} [{u.role}]
              </option>
            ))
          )}
        </select>
      </div>
    </header>
  );
}

export function MetroFooter() {
  return (
    <footer
      className="metro-glass-footer"
      style={{
        background:
          "linear-gradient(99.79deg, rgba(255, 255, 255, 0.92) 1.95%, rgba(255, 255, 255, 0.78) 96.47%)",
        backdropFilter: "blur(20px) saturate(180%)",
        borderTop: "1px solid #d1d1d1",
        padding: "14px 28px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "12px",
        marginTop: "32px",
      }}
    >
      <div style={{ fontSize: "13px", color: "#323232", fontWeight: 600 }}>
        COPYRIGHT © 2026{" "}
        <a
          href="https://www.metro-gsc.in/"
          target="_blank"
          rel="noreferrer"
          style={{ color: METRO_COLORS.primaryNavy, fontWeight: 800, textDecoration: "none" }}
        >
          Metro GSC
        </a>
        , All rights Reserved
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span style={{ fontSize: "13px", color: "#4f4f4f", fontWeight: 700 }}>Powered By:</span>
        <a
          href="https://www.metro-gsc.in/"
          target="_blank"
          rel="noreferrer"
          style={{ display: "inline-flex", alignItems: "center" }}
        >
          <img
            src={METRO_GSC_LOGO_DATA_URL}
            alt="METRO Global Solution Center"
            style={{ height: "32px", width: "auto", display: "block" }}
          />
        </a>
      </div>
    </footer>
  );
}
