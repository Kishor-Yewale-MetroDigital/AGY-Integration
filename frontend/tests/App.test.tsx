import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App, { formatINR } from "../src/App";

describe("TalentFlow Frontend Suite", () => {
  it("formats INR values accurately into Crores and Lakhs", () => {
    expect(formatINR("15760000.00")).toBe("₹1.58 Cr");
    expect(formatINR("4500000.00")).toBe("₹45.00 L");
    expect(formatINR("50000.00")).toBe("₹50,000.00");
  });

  it("renders Executive Overview KPIs and navigates across all 5 modules", () => {
    render(<App />);
    expect(
      screen.getByText(/TalentFlow — Enterprise Hiring & People Committee Platform/i)
    ).toBeDefined();
    expect(screen.getByText(/Total Requests/i)).toBeDefined();
    expect(screen.getByText(/Pending Committee/i)).toBeDefined();
    expect(screen.getAllByText(/Approved Positions/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Monthly Hiring Request Trend/i)).toBeDefined();
    expect(screen.getByText(/Job Grade Distribution/i)).toBeDefined();

    // Navigate to Hiring Requests tab
    fireEvent.click(screen.getByText(/Hiring Requests \(/i));
    expect(screen.getByText(/Create New Hiring Requisition/i)).toBeDefined();
    expect(screen.getByText(/Save as Draft/i)).toBeDefined();

    // Navigate to People Committee Queue tab
    fireEvent.click(screen.getByText(/People Committee Queue/i));
    expect(
      screen.getByText(/People Committee & Multi-Stage Approval Queue/i)
    ).toBeDefined();
    expect(
      screen.getByText(/Auto-Select Authorized Stage Approver/i)
    ).toBeDefined();
    expect(screen.getByText(/Delegate Stage Approval Authority/i)).toBeDefined();
    expect(
      screen.getByText(/Configurable Governance & Approval Rules/i)
    ).toBeDefined();

    // Navigate to Workforce & Cost Planning tab
    fireEvent.click(screen.getByText(/Workforce & Cost Planning/i));
    expect(
      screen.getByText(/Department Budget Envelope vs. Commitments/i)
    ).toBeDefined();
    expect(screen.getByText(/Vacancy Delay Simulation/i)).toBeDefined();

    // Navigate to Immutable Audit Log tab
    fireEvent.click(screen.getByText(/Immutable Audit Log/i));
    expect(screen.getByText(/Immutable Governance Audit Log/i)).toBeDefined();
  });
});
