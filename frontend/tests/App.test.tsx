import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App, { formatINR } from "../src/App";

describe("TalentFlow Frontend Suite", () => {
  it("formats INR values accurately into Crores and Lakhs", () => {
    expect(formatINR("15760000.00")).toBe("₹1.58 Cr");
    expect(formatINR("4500000.00")).toBe("₹45.00 L");
  });

  it("renders Executive Overview KPIs and navigates across modules", () => {
    render(<App />);
    expect(
      screen.getByText(/TalentFlow — Enterprise Hiring & People Committee Platform/i)
    ).toBeDefined();
    expect(screen.getByText(/Total Requests/i)).toBeDefined();
    expect(screen.getByText(/Pending Committee/i)).toBeDefined();
    expect(screen.getByText(/Approved Positions/i)).toBeDefined();

    fireEvent.click(screen.getByText(/People Committee Queue/i));
    expect(
      screen.getByText(/People Committee & Multi-Stage Approval Queue/i)
    ).toBeDefined();
  });
});
