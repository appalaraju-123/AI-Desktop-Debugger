"""
Export engine for Debugging Report & Performance Analysis (Module 5).
Supports exporting reports as Markdown (.md), HTML (.html), and Plain Text (.txt).
"""

import html
from src.report.models import DebugReport


class ReportExporter:
    """
    Serializes DebugReport instances into Markdown, HTML, and Plain Text formats.
    """

    @classmethod
    def to_markdown(cls, report: DebugReport) -> str:
        """Generates a structured GitHub-flavored Markdown report."""
        lines: list[str] = []

        # Header
        lines.append(f"# 📊 Debugging & Performance Report")
        lines.append(f"**Generated:** {report.timestamp} | **Status:** `{report.status}`\n")

        # 1. Summary
        lines.append("## 📋 Overall Summary")
        lines.append(f"> {report.summary}\n")

        # 2. Program & Environment Information
        lines.append("## 📁 Program Information")
        lines.append("| Property | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| **Source File** | `{report.file_name}` |")
        if report.file_path:
            lines.append(f"| **File Path** | `{report.file_path}` |")
        lines.append(f"| **Language** | {report.language} |")
        lines.append(f"| **Total Lines** | {report.total_lines} |")
        lines.append(f"| **Execution Status** | `{report.status}` |")
        lines.append("")

        # 3. Execution & Performance Analysis
        lines.append("## ⚙️ Execution & Performance Analysis")
        p = report.performance
        lines.append("| Metric | Value | Details |")
        lines.append("| :--- | :--- | :--- |")
        lines.append(f"| **Execution Time** | `{p.execution_time:.3f}s` | Elapsed wall-clock time |")
        lines.append(f"| **Execution Stage** | `{p.execution_stage}` | Cycle phase reached |")
        lines.append(f"| **Exit Code** | `{p.exit_code}` | Process return code |")
        lines.append(f"| **Execution-Time Indicator** | `{p.speed_rating}` | Simple execution-time indicator (not a true hardware benchmark) |")
        lines.append(f"| **Memory** | `{p.memory_note}` | Memory tracking not active |")
        lines.append("")

        # 4. Error Diagnostics (if error occurred)
        if report.error_info:
            err = report.error_info
            lines.append("## 🚨 Error Diagnostics")
            lines.append("| Diagnostic Field | Information |")
            lines.append("| :--- | :--- |")
            lines.append(f"| **Category** | {err.error_category} |")
            lines.append(f"| **Error Type** | `{err.error_type}` |")
            lines.append(f"| **Severity** | `{err.severity}` |")
            loc_str = f"Line {err.line_number}" if err.line_number else "Unknown"
            if err.column_number:
                loc_str += f", Column {err.column_number}"
            lines.append(f"| **Location** | {loc_str} |")
            lines.append(f"| **Message** | {err.message} |")
            lines.append("")

            if err.code_context:
                lines.append("### Code Context")
                lines.append("```")
                lines.append(err.code_context)
                lines.append("```\n")

            if err.raw_details:
                lines.append("### Raw Traceback / Compiler Output")
                lines.append("```")
                lines.append(err.raw_details.strip())
                lines.append("```\n")
        else:
            lines.append("## 🚨 Error Diagnostics")
            lines.append("No errors or exceptions were detected during execution.\n")

        # 5. AI Diagnosis & Recommendations (if present)
        if report.ai_analysis:
            ai = report.ai_analysis
            lines.append("## ✨ AI Diagnosis & Recommendations")
            lines.append("### 🔍 Root Cause Analysis")
            lines.append(f"{ai.root_cause}\n")

            if ai.suggested_fix:
                lang_code = report.language.lower()
                lang_tag = "python" if "python" in lang_code else ("javascript" if "javascript" in lang_code else lang_code)
                lines.append("### 🛠️ Suggested Fix (Review Only)")
                if ai.explanation:
                    lines.append(f"*{ai.explanation}*\n")
                lines.append(f"```{lang_tag}")
                lines.append(ai.suggested_fix.strip())
                lines.append("```\n")

            if ai.debugging_guidance:
                lines.append("### 💡 Debugging Guidance & Prevention")
                for tip in ai.debugging_guidance:
                    lines.append(f"- {tip}")
                lines.append("")

            if ai.optimized_solution:
                lines.append("### ⚡ Alternative / Optimized Approach")
                lines.append(f"```{lang_tag}")
                lines.append(ai.optimized_solution.strip())
                lines.append("```\n")
        elif report.error_info:
            lines.append("## ✨ AI Diagnosis & Recommendations")
            lines.append("*AI analysis was not requested for this run. Press **F8** or click '✨ Explain with AI' to generate AI diagnostics.*\n")

        # 6. Raw Console Output
        lines.append("## 📜 Execution Console Output")
        res = report.execution_result
        if res.stdout:
            lines.append("### Standard Output (stdout)")
            lines.append("```")
            lines.append(res.stdout.strip())
            lines.append("```\n")

        if res.stderr:
            lines.append("### Standard Error (stderr)")
            lines.append("```")
            lines.append(res.stderr.strip())
            lines.append("```\n")

        lines.append("---\n*Report generated by AI-Based Intelligent Desktop Debugger.*")
        return "\n".join(lines)

    @classmethod
    def to_html(cls, report: DebugReport) -> str:
        """Generates a standalone, dark-themed HTML document suitable for web browsers or printing."""
        res = report.execution_result
        perf = report.performance
        err = report.error_info
        ai = report.ai_analysis

        status_colors = {
            "SUCCESS": "#2ea043",
            "RUNTIME_ERROR": "#f85149",
            "COMPILATION_ERROR": "#d29922",
            "TIMEOUT": "#db6d28",
            "ENVIRONMENT_ERROR": "#a371f7",
        }
        badge_bg = status_colors.get(report.status, "#565b61")

        loc_str = "None"
        if err and err.line_number:
            loc_str = f"Line {err.line_number}"
            if err.column_number:
                loc_str += f", Col {err.column_number}"

        html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Debug Report - {html.escape(report.file_name)}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #0d1117;
    color: #c9d1d9;
    line-height: 1.6;
    margin: 0;
    padding: 24px;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 32px;
  }}
  h1, h2, h3 {{
    color: #f0f6fc;
    margin-top: 24px;
    margin-bottom: 12px;
    border-bottom: 1px solid #21262d;
    padding-bottom: 8px;
  }}
  h1 {{ font-size: 24px; margin-top: 0; display: flex; align-items: center; justify-content: space-between; }}
  .badge {{
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 12px;
    color: #ffffff;
    font-weight: bold;
    display: inline-block;
  }}
  .summary-card {{
    background-color: #1f242c;
    border-left: 4px solid {badge_bg};
    padding: 14px 18px;
    border-radius: 4px;
    margin: 16px 0;
    font-size: 14px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
  }}
  th, td {{
    text-align: left;
    padding: 8px 12px;
    border: 1px solid #30363d;
    font-size: 13px;
  }}
  th {{
    background-color: #21262d;
    color: #8b949e;
  }}
  pre, code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
  }}
  code {{
    background-color: #21262d;
    padding: 2px 6px;
    border-radius: 4px;
    color: #79c0ff;
  }}
  pre {{
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    color: #e6edf3;
  }}
  .card {{
    background-color: #1c2128;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 14px;
  }}
  .tip-list {{
    margin: 8px 0;
    padding-left: 20px;
  }}
  .tip-list li {{
    margin-bottom: 6px;
  }}
  .footer {{
    margin-top: 32px;
    text-align: center;
    font-size: 12px;
    color: #8b949e;
    border-top: 1px solid #21262d;
    padding-top: 16px;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>
    <span>📊 Debugging & Performance Report</span>
    <span class="badge" style="background-color: {badge_bg};">{report.status}</span>
  </h1>
  <div style="font-size: 12px; color: #8b949e; margin-bottom: 16px;">
    Generated on: <strong>{html.escape(report.timestamp)}</strong> &bull; File: <strong>{html.escape(report.file_name)}</strong>
  </div>

  <h2>📋 Overall Summary</h2>
  <div class="summary-card">
    {html.escape(report.summary)}
  </div>

  <h2>📁 Program Information</h2>
  <table>
    <tr><th>Property</th><th>Value</th></tr>
    <tr><td><strong>Source File</strong></td><td><code>{html.escape(report.file_name)}</code></td></tr>
    {f"<tr><td><strong>File Path</strong></td><td><code>{html.escape(report.file_path or '')}</code></td></tr>" if report.file_path else ""}
    <tr><td><strong>Language</strong></td><td>{html.escape(report.language)}</td></tr>
    <tr><td><strong>Total Lines</strong></td><td>{report.total_lines}</td></tr>
    <tr><td><strong>Execution Status</strong></td><td><span class="badge" style="background-color: {badge_bg};">{report.status}</span></td></tr>
  </table>

  <h2>⚙️ Execution & Performance Analysis</h2>
  <table>
    <tr><th>Metric</th><th>Value</th><th>Details</th></tr>
    <tr><td><strong>Execution Time</strong></td><td><code>{perf.execution_time:.3f}s</code></td><td>Elapsed wall-clock time</td></tr>
    <tr><td><strong>Execution Stage</strong></td><td><code>{html.escape(perf.execution_stage)}</code></td><td>Execution lifecycle phase reached</td></tr>
    <tr><td><strong>Exit Code</strong></td><td><code>{perf.exit_code}</code></td><td>Process return code</td></tr>
    <tr><td><strong>Execution-Time Indicator</strong></td><td>{html.escape(perf.speed_rating)}</td><td>Simple execution-time indicator (not a true hardware benchmark)</td></tr>
    <tr><td><strong>Memory</strong></td><td>{html.escape(perf.memory_note)}</td><td>Memory tracking not active</td></tr>
  </table>
"""

        # Diagnostics section
        if err:
            html_out += f"""
  <h2>🚨 Error Diagnostics</h2>
  <table>
    <tr><th>Field</th><th>Information</th></tr>
    <tr><td><strong>Category</strong></td><td>{html.escape(err.error_category)}</td></tr>
    <tr><td><strong>Error Type</strong></td><td><code>{html.escape(err.error_type)}</code></td></tr>
    <tr><td><strong>Severity</strong></td><td><strong>{html.escape(err.severity)}</strong></td></tr>
    <tr><td><strong>Location</strong></td><td>{html.escape(loc_str)}</td></tr>
    <tr><td><strong>Message</strong></td><td>{html.escape(err.message)}</td></tr>
  </table>
"""
            if err.code_context:
                html_out += f"""
  <h3>Code Context</h3>
  <pre>{html.escape(err.code_context)}</pre>
"""
            if err.raw_details:
                html_out += f"""
  <h3>Raw Output Details</h3>
  <pre>{html.escape(err.raw_details.strip())}</pre>
"""
        else:
            html_out += """
  <h2>🚨 Error Diagnostics</h2>
  <div class="card" style="color: #7ee787;">
    ✓ Program completed cleanly without compiler or runtime exceptions.
  </div>
"""

        # AI section
        if ai:
            html_out += f"""
  <h2>✨ AI Diagnosis & Recommendations</h2>
  <div class="card">
    <h3 style="margin-top:0; color:#ff7b72;">🔍 Root Cause Analysis</h3>
    <p>{html.escape(ai.root_cause)}</p>
"""
            if ai.suggested_fix:
                html_out += f"""
    <h3 style="color:#79c0ff;">🛠️ Suggested Fix (Review Only)</h3>
    {f"<p><em>{html.escape(ai.explanation)}</em></p>" if ai.explanation else ""}
    <pre style="color:#7ee787;">{html.escape(ai.suggested_fix.strip())}</pre>
"""
            if ai.debugging_guidance:
                html_out += """
    <h3 style="color:#d2a8ff;">💡 Debugging Guidance & Prevention</h3>
    <ul class="tip-list">
"""
                for tip in ai.debugging_guidance:
                    html_out += f"      <li>{html.escape(tip)}</li>\n"
                html_out += "    </ul>\n"

            if ai.optimized_solution:
                html_out += f"""
    <h3 style="color:#56d364;">⚡ Alternative / Optimized Approach</h3>
    <pre style="color:#d2a8ff;">{html.escape(ai.optimized_solution.strip())}</pre>
"""
            html_out += "  </div>\n"
        elif err:
            html_out += """
  <h2>✨ AI Diagnosis & Recommendations</h2>
  <div class="card" style="color: #8b949e; font-style: italic;">
    AI diagnosis has not been requested for this run. Press <strong>F8</strong> or click '✨ Explain with AI' in the Output tab.
  </div>
"""

        # Output console
        html_out += "  <h2>📜 Console Output</h2>\n"
        if res.stdout:
            html_out += f"  <h3>Standard Output (stdout)</h3>\n  <pre>{html.escape(res.stdout.strip())}</pre>\n"
        if res.stderr:
            html_out += f"  <h3>Standard Error (stderr)</h3>\n  <pre style='color:#f85149;'>{html.escape(res.stderr.strip())}</pre>\n"
        if not res.stdout and not res.stderr:
            html_out += "  <div class='card' style='color:#8b949e;'>[No console output generated]</div>\n"

        html_out += """  <div class="footer">
    Report generated by AI-Based Intelligent Desktop Debugger
  </div>
</div>
</body>
</html>
"""
        return html_out

    @classmethod
    def to_text(cls, report: DebugReport) -> str:
        """Generates a plain-text ASCII layout of the report."""
        sep = "=" * 76
        sub_sep = "-" * 76
        lines: list[str] = [
            sep,
            "                   AI DEBUGGING & PERFORMANCE REPORT",
            sep,
            f"Generated: {report.timestamp} | Status: {report.status}",
            sub_sep,
            f"Source File:     {report.file_name}",
            f"File Path:       {report.file_path or 'Untitled Buffer'}",
            f"Language:        {report.language}",
            f"Total Lines:     {report.total_lines}",
            sub_sep,
            "OVERALL SUMMARY:",
            f"  {report.summary}",
            sub_sep,
            "EXECUTION & PERFORMANCE ANALYSIS:",
            f"  • Execution Time:           {report.performance.execution_time:.3f}s",
            f"  • Stage:                    {report.performance.execution_stage}",
            f"  • Exit Code:                {report.performance.exit_code}",
            f"  • Execution-Time Indicator: {report.performance.speed_rating}",
            f"  • Memory:                   {report.performance.memory_note}",
            sub_sep,
        ]

        if report.error_info:
            err = report.error_info
            loc = f"Line {err.line_number}" if err.line_number else "Unknown"
            if err.column_number:
                loc += f", Col {err.column_number}"
            lines.extend([
                "DIAGNOSTIC ERROR DETAILS:",
                f"  • Category:  {err.error_category}",
                f"  • Type:      {err.error_type}",
                f"  • Severity:  {err.severity}",
                f"  • Location:  {loc}",
                f"  • Message:   {err.message}",
            ])
            if err.code_context:
                lines.extend([
                    "",
                    "  Code Context:",
                    f"    {err.code_context.strip()}",
                ])
            if err.raw_details:
                lines.extend([
                    "",
                    "  Traceback / Compiler Details:",
                    "\n".join(f"    {l}" for l in err.raw_details.strip().splitlines()),
                ])
            lines.append(sub_sep)
        else:
            lines.extend([
                "DIAGNOSTIC ERROR DETAILS:",
                "  No errors or exceptions detected during execution.",
                sub_sep,
            ])

        if report.ai_analysis:
            ai = report.ai_analysis
            lines.extend([
                "AI DIAGNOSIS & RECOMMENDATIONS:",
                "  Root Cause Analysis:",
                f"    {ai.root_cause}",
            ])
            if ai.suggested_fix:
                lines.extend([
                    "",
                    "  Suggested Code Fix (Review Only):",
                    f"    Explanation: {ai.explanation or 'None'}",
                    "\n".join(f"    {l}" for l in ai.suggested_fix.strip().splitlines()),
                ])
            if ai.debugging_guidance:
                lines.extend([
                    "",
                    "  Debugging Guidance & Prevention:",
                ])
                for tip in ai.debugging_guidance:
                    lines.append(f"    • {tip}")
            if ai.optimized_solution:
                lines.extend([
                    "",
                    "  Optimized Solution:",
                    "\n".join(f"    {l}" for l in ai.optimized_solution.strip().splitlines()),
                ])
            lines.append(sub_sep)

        lines.extend([
            "OUTPUT LOGS:",
            f"  stdout: {report.execution_result.stdout.strip() or '[empty]'}",
            f"  stderr: {report.execution_result.stderr.strip() or '[empty]'}",
            sep,
        ])

        return "\n".join(lines)
