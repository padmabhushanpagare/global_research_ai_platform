import json
from jinja2 import Template

# 1. Simulating the verified clean output from your Ollama step
ollama_json_data = """
{
"ticker": "TSLA",
"quarter": "Q1 2026",
"revenue_billions": 22.4,
"eps": 0.15,
"guidance": "Management expects delivery volume growth to accelerate in the second half of the fiscal year, driven by next-generation vehicle production ramping up.",
"sentiment": "Bullish",
"key_takeaways": ["Tesla reported revenue of $22.4 billion for Q1 2026", "Net income attributable to common stockholders was $477 million", "EPS was $0.15"]
}
"""

def build_html_report(json_str):
    # Safely convert string to Python dictionary
    data = json.loads(json_str)
    
    # Load the HTML structure
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
                <div class="metric">${{ revenue_billions }}B</div>
            </div>
            <div class="card">
                <div style="font-weight: bold; color: #666;">Earnings Per Share (EPS)</div>
                <div class="metric">${{ eps }}</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 25px;">
            <h3 class="section-title" style="margin-top: 0;">Forward-Looking Guidance</h3>
            <p>{{ guidance }}</p>
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
    
    # Compile and render template with data
    template = Template(html_template)
    rendered_html = template.render(data)
    
    # Save the output file
    output_filename = f"{data['ticker']}_Report.html"
    with open(output_filename, "w") as f:
        f.write(rendered_html)
    
    print(f"Success: Professional HTML report generated as '{output_filename}'!")

if __name__ == "__main__":
    build_html_report(ollama_json_data)