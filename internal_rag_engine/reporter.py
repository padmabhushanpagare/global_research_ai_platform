from jinja2 import Template

def build_html_report(data):
    """Compiles clean Python data dictionary values straight into a Jinja2 template."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; color: #333; line-height: 1.6; }
            .header { border-bottom: 3px solid #E2231A; padding-bottom: 10px; margin-bottom: 25px; }
            .ticker { background: #E2231A; color: white; padding: 4px 10px; font-weight: bold; border-radius: 3px; font-size: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }
            .card { border: 1px solid #e0e0e0; padding: 20px; border-radius: 6px; background: #fafafa; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .metric { font-size: 28px; font-weight: bold; color: #E2231A; margin-top: 5px; }
            .section-title { color: #111; border-left: 4px solid #E2231A; padding-left: 10px; margin-top: 20px; }
            ul { padding-left: 20px; }
            li { margin-bottom: 8px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2><span class="ticker">{{ ticker }}</span> Equity Research Tear-Sheet</h2>
            <p><strong>Fiscal Period:</strong> {{ quarter }} | <strong>Pipeline Sentiment:</strong> {{ sentiment }}</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <div style="font-weight: bold; color: #666;">Quarterly Revenue</div>
                <div class="metric">{{ display_revenue }}</div>
            </div>
            <div class="card">
                <div style="font-weight: bold; color: #666;">Earnings Per Share (EPS)</div>
                <div class="metric">{{ display_eps }}</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 25px;">
            <h3 class="section-title" style="margin-top: 0;">Forward-Looking Guidance</h3>
            <p>{{ guidance if guidance else "No operational guidance targeted or itemized within text inputs." }}</p>
        </div>

        <div class="card">
            <h3 class="section-title" style="margin-top: 0;">Automated Key Takeaways</h3>
            <ul>
                {% for takeaway in key_takeaways %}
                    <li>{{ takeaway }}</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """
    
    display_data = data.copy()
    
    if display_data.get('revenue_billions') is not None:
        display_data['display_revenue'] = f"${display_data['revenue_billions']}B"
    else:
        display_data['display_revenue'] = "N/A"
        
    if display_data.get('eps') is not None:
        display_data['display_eps'] = f"${display_data['eps']}"
    else:
        display_data['display_eps'] = "N/A"

    # Make sure to pass display_data to the template, not the raw data!
    template = Template(html_template)
    rendered_html = template.render(display_data)
    
    output_filename = f"{data.get('ticker', 'UNKNOWN')}_Report.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    
    print(f"[=>] Success: Professional HTML report generated as '{output_filename}'!")
    return output_filename