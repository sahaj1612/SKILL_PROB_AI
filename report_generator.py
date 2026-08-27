import pdfkit
from io import BytesIO
from datetime import datetime
import os
import tempfile

class ReportGenerator:
    @staticmethod
    def generate_html_report(session_data, performance_data, answers_data):
        """Generate HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate average scores
        if answers_data:
            avg_grammar = sum(a.get('grammar_score', 0) for a in answers_data) / len(answers_data)
            avg_relevance = sum(a.get('relevance_score', 0) for a in answers_data) / len(answers_data)
            avg_confidence = sum(a.get('confidence_score', 0) for a in answers_data) / len(answers_data)
        else:
            avg_grammar = avg_relevance = avg_confidence = 0
        
        # Prepare answers table rows
        answers_rows = ""
        if answers_data:
            for answer in answers_data:
                answers_rows += f"""
                    <tr>
                        <td>{answer.get('question_text', 'N/A')[:50]}...</td>
                        <td>{answer.get('grammar_score', 0)}/10</td>
                        <td>{answer.get('relevance_score', 0)}/10</td>
                        <td>{answer.get('confidence_score', 0)}/10</td>
                        <td>{answer.get('feedback', '')[:50]}...</td>
                    </tr>
                """
        else:
            answers_rows = "<tr><td colspan='5'>No answers recorded</td></tr>"
        
        # Prepare strengths list
        strengths_list = ""
        for strength in performance_data.get('strengths', []):
            strengths_list += f'<li>{strength}</li>'
        
        # Prepare weaknesses list
        weaknesses_list = ""
        for weakness in performance_data.get('weaknesses', []):
            weaknesses_list += f'<li>{weakness}</li>'
        
        # Prepare improvement plan
        improvement_plan = ""
        for item in performance_data.get('improvement_plan', []):
            improvement_plan += f'<li>{item}</li>'
        
        # Determine verdict color
        verdict = performance_data.get('final_verdict', 'Not Evaluated')
        if verdict == 'Strong Candidate':
            verdict_color = '#d4edda'
        elif verdict == 'Needs Improvement':
            verdict_color = '#fff3cd'
        else:
            verdict_color = '#f8d7da'
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Interview Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .score-card {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 25px; 
            border-radius: 10px; 
            margin: 25px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .section {{ 
            margin: 30px 0; 
            padding: 25px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
            background: #fff;
        }}
        .strengths {{ color: #28a745; font-weight: 500; }}
        .weaknesses {{ color: #e74c3c; font-weight: 500; }}
        .progress-bar {{ 
            background-color: #e0e0e0; 
            border-radius: 10px; 
            height: 20px; 
            margin: 10px 0;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{ 
            height: 100%; 
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            text-align: center;
            color: white;
            line-height: 20px;
            font-size: 12px;
            transition: width 0.3s ease;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{ 
            padding: 12px 15px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }}
        th {{ 
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{ background-color: #f5f5f5; }}
        .verdict {{ 
            font-size: 22px; 
            font-weight: bold; 
            text-align: center; 
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            background-color: {verdict_color};
            color: #333;
        }}
        .metric-score {{ 
            font-size: 24px; 
            font-weight: bold; 
            color: #2c3e50;
        }}
        .subtitle {{ 
            color: #7f8c8d; 
            font-size: 14px; 
            margin-top: 5px;
        }}
        .print-button {{
            display: none;
        }}
        @media print {{
            .print-button {{ display: none !important; }}
            body {{ margin: 10px; }}
            .section {{ border: 1px solid #ccc; }}
            a {{ text-decoration: none; color: #000; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Interview Performance Report</h1>
        <p>Generated on: {timestamp}</p>
        <p><strong>Domain:</strong> {session_data.get('domain', 'N/A')} | 
           <strong>Level:</strong> {session_data.get('experience_level', 'N/A')}</p>
    </div>
    
    <div class="score-card">
        <h2>Overall Score: {performance_data.get('overall_score', 0)}/100</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {performance_data.get('overall_score', 0)}%">
                {performance_data.get('overall_score', 0)}%
            </div>
        </div>
        <div class="verdict">
            Final Verdict: {verdict}
        </div>
    </div>
    
    <div class="section">
        <h3>📈 Performance Metrics</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Score</th>
                <th>Progress</th>
            </tr>
            <tr>
                <td>Communication Skills</td>
                <td class="metric-score">{performance_data.get('communication_score', 0)}/10</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {performance_data.get('communication_score', 0) * 10}%"></div>
                    </div>
                </td>
            </tr>
            <tr>
                <td>Technical Knowledge</td>
                <td class="metric-score">{performance_data.get('technical_score', 0)}/10</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {performance_data.get('technical_score', 0) * 10}%"></div>
                    </div>
                </td>
            </tr>
            <tr>
                <td>Confidence Level</td>
                <td class="metric-score">{performance_data.get('confidence_score', 0)}/10</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {performance_data.get('confidence_score', 0) * 10}%"></div>
                    </div>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h3>✅ Strengths</h3>
        <ul class="strengths">
            {strengths_list if strengths_list else '<li>No specific strengths identified</li>'}
        </ul>
        
        <h3>📝 Areas for Improvement</h3>
        <ul class="weaknesses">
            {weaknesses_list if weaknesses_list else '<li>No specific weaknesses identified</li>'}
        </ul>
    </div>
    
    <div class="section">
        <h3>💬 Question Analysis</h3>
        <table>
            <tr>
                <th>Question</th>
                <th>Grammar</th>
                <th>Relevance</th>
                <th>Confidence</th>
                <th>Feedback</th>
            </tr>
            {answers_rows}
        </table>
        <p class="subtitle">Average Scores: Grammar: {avg_grammar:.1f}/10 | Relevance: {avg_relevance:.1f}/10 | Confidence: {avg_confidence:.1f}/10</p>
    </div>
    
    <div class="section">
        <h3>🎯 Improvement Plan</h3>
        <ol>
            {improvement_plan if improvement_plan else '<li>No specific improvement plan available</li>'}
        </ol>
    </div>
    
    <div class="section">
        <h3>📋 Detailed Analysis</h3>
        <p>{performance_data.get('detailed_analysis', 'No detailed analysis available.')}</p>
    </div>
    
    <div class="section">
        <p><strong>Note:</strong> This report is generated by AI and should be used as a guide for improvement.
        Regular practice and mock interviews will help improve performance.</p>
        <p class="subtitle">Report generated using AI Interview Coach System</p>
    </div>
    
    <button class="print-button" onclick="window.print()">Print Report</button>
    
    <script>
        // Add print functionality
        document.addEventListener('DOMContentLoaded', function() {{
            const printBtn = document.querySelector('.print-button');
            if (printBtn) {{
                printBtn.style.display = 'block';
                printBtn.style.margin = '20px auto';
                printBtn.style.padding = '10px 20px';
                printBtn.style.background = '#007bff';
                printBtn.style.color = 'white';
                printBtn.style.border = 'none';
                printBtn.style.borderRadius = '5px';
                printBtn.style.cursor = 'pointer';
            }}
        }});
    </script>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def generate_pdf(html_content, output_path=None):
        """Convert HTML to PDF using pdfkit"""
        if output_path is None:
            output_path = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        try:
            # Try with different wkhtmltopdf configurations
            config = None
            
            # Check common wkhtmltopdf installation paths
            possible_paths = [
                '/usr/local/bin/wkhtmltopdf',
                '/usr/bin/wkhtmltopdf',
                'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe',
                'C:/Program Files (x86)/wkhtmltopdf/bin/wkhtmltopdf.exe',
                os.path.expanduser('~/wkhtmltopdf/bin/wkhtmltopdf')
            ]
            
            # Find wkhtmltopdf executable
            wkhtmltopdf_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    wkhtmltopdf_path = path
                    break
            
            if wkhtmltopdf_path:
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                print(f"Using wkhtmltopdf at: {wkhtmltopdf_path}")
            else:
                print("wkhtmltopdf not found in common locations. Trying default...")
            
            # PDF generation options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,  # Allow local file access
            }
            
            # Generate PDF
            if config:
                pdfkit.from_string(html_content, output_path, options=options, configuration=config)
            else:
                pdfkit.from_string(html_content, output_path, options=options)
            
            print(f"PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating PDF with pdfkit: {e}")
            
            # Fallback: Save as HTML file
            try:
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Saved as HTML instead: {html_path}")
                return html_path
            except Exception as html_error:
                print(f"Error saving HTML: {html_error}")
                return None
    
    @staticmethod
    def generate_pdf_simple(html_content, output_path=None):
        """Simple PDF generation without external dependencies"""
        if output_path is None:
            output_path = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Simple fallback: just save as HTML
        try:
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"PDF generation not available. Saved as HTML: {html_path}")
            print("To enable PDF generation, please install:")
            print("1. wkhtmltopdf from https://wkhtmltopdf.org/downloads.html")
            print("2. Then install pdfkit: pip install pdfkit")
            return html_path
        except Exception as e:
            print(f"Error saving report: {e}")
            return None

# from xhtml2pdf import pisa
# import pdfkit
# from io import BytesIO
# from datetime import datetime
# import os

# class ReportGenerator:
#     @staticmethod
#     def generate_html_report(session_data, performance_data, answers_data, coding_data):
#         """Generate HTML report"""
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         # Calculate average scores
#         avg_grammar = sum(a.get('grammar_score', 0) for a in answers_data) / max(len(answers_data), 1)
#         avg_relevance = sum(a.get('relevance_score', 0) for a in answers_data) / max(len(answers_data), 1)
#         avg_confidence = sum(a.get('confidence_score', 0) for a in answers_data) / max(len(answers_data), 1)
        
#         html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="UTF-8">
#             <title>Interview Performance Report</title>
#             <style>
#                 body {{ font-family: Arial, sans-serif; margin: 40px; }}
#                 .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
#                 .score-card {{ 
#                     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                     color: white; 
#                     padding: 20px; 
#                     border-radius: 10px; 
#                     margin: 20px 0;
#                     box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#                 }}
#                 .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
#                 .strengths {{ color: green; }}
#                 .weaknesses {{ color: #e74c3c; }}
#                 .progress-bar {{ 
#                     background-color: #e0e0e0; 
#                     border-radius: 10px; 
#                     height: 20px; 
#                     margin: 10px 0;
#                     overflow: hidden;
#                 }}
#                 .progress-fill {{ 
#                     height: 100%; 
#                     background: linear-gradient(90deg, #4CAF50, #8BC34A);
#                     text-align: center;
#                     color: white;
#                     line-height: 20px;
#                 }}
#                 table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
#                 th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
#                 th {{ background-color: #f2f2f2; }}
#                 .verdict {{ 
#                     font-size: 24px; 
#                     font-weight: bold; 
#                     text-align: center; 
#                     padding: 20px;
#                     margin: 20px 0;
#                     border-radius: 5px;
#                     background-color: {'#d4edda' if performance_data.get('final_verdict') == 'Strong Candidate' else 
#                                       '#fff3cd' if performance_data.get('final_verdict') == 'Needs Improvement' else 
#                                       '#f8d7da'};
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="header">
#                 <h1>📊 Interview Performance Report</h1>
#                 <p>Generated on: {timestamp}</p>
#                 <p>Domain: {session_data.get('domain', 'N/A')} | 
#                    Level: {session_data.get('experience_level', 'N/A')}</p>
#             </div>
            
#             <div class="score-card">
#                 <h2>Overall Score: {performance_data.get('overall_score', 0)}/100</h2>
#                 <div class="progress-bar">
#                     <div class="progress-fill" style="width: {performance_data.get('overall_score', 0)}%">
#                         {performance_data.get('overall_score', 0)}%
#                     </div>
#                 </div>
#                 <div class="verdict">
#                     Verdict: {performance_data.get('final_verdict', 'Not Evaluated')}
#                 </div>
#             </div>
            
#             <div class="section">
#                 <h3>📈 Performance Metrics</h3>
#                 <table>
#                     <tr>
#                         <th>Metric</th>
#                         <th>Score</th>
#                         <th>Progress</th>
#                     </tr>
#                     <tr>
#                         <td>Communication</td>
#                         <td>{performance_data.get('communication_score', 0)}/10</td>
#                         <td>
#                             <div class="progress-bar">
#                                 <div class="progress-fill" style="width: {performance_data.get('communication_score', 0)*10}%"></div>
#                             </div>
#                         </td>
#                     </tr>
#                     <tr>
#                         <td>Technical Knowledge</td>
#                         <td>{performance_data.get('technical_score', 0)}/10</td>
#                         <td>
#                             <div class="progress-bar">
#                                 <div class="progress-fill" style="width: {performance_data.get('technical_score', 0)*10}%"></div>
#                             </div>
#                         </td>
#                     </tr>
#                     <tr>
#                         <td>Confidence</td>
#                         <td>{performance_data.get('confidence_score', 0)}/10</td>
#                         <td>
#                             <div class="progress-bar">
#                                 <div class="progress-fill" style="width: {performance_data.get('confidence_score', 0)*10}%"></div>
#                             </div>
#                         </td>
#                     </tr>
#                 </table>
#             </div>
            
#             <div class="section">
#                 <h3>✅ Strengths</h3>
#                 <ul class="strengths">
#         """
        
#         for strength in performance_data.get('strengths', []):
#             html += f'<li>{strength}</li>'
        
#         html += """
#                 </ul>
                
#                 <h3>📝 Areas for Improvement</h3>
#                 <ul class="weaknesses">
#         """
        
#         for weakness in performance_data.get('weaknesses', []):
#             html += f'<li>{weakness}</li>'
        
#         html += """
#                 </ul>
#             </div>
            
#             <div class="section">
#                 <h3>💬 Question Analysis</h3>
#                 <table>
#                     <tr>
#                         <th>Question</th>
#                         <th>Grammar</th>
#                         <th>Relevance</th>
#                         <th>Confidence</th>
#                         <th>Feedback</th>
#                     </tr>
#         """
        
#         for answer in answers_data:
#             html += f"""
#                     <tr>
#                         <td>{answer.get('question_text', 'N/A')[:50]}...</td>
#                         <td>{answer.get('grammar_score', 0)}/10</td>
#                         <td>{answer.get('relevance_score', 0)}/10</td>
#                         <td>{answer.get('confidence_score', 0)}/10</td>
#                         <td>{answer.get('feedback', '')[:50]}...</td>
#                     </tr>
#             """
        
#         html += """
#                 </table>
#             </div>
            
#             <div class="section">
#                 <h3>🎯 Improvement Plan</h3>
#                 <ol>
#         """
        
#         for item in performance_data.get('improvement_plan', []):
#             html += f'<li>{item}</li>'
        
#         html += """
#                 </ol>
#             </div>
            
#             <div class="section">
#                 <h3>📋 Detailed Analysis</h3>
#                 <p>{}</p>
#             </div>
            
#             <div class="section">
#                 <p><strong>Note:</strong> This report is generated by AI and should be used as a guide for improvement.
#                 Regular practice and mock interviews will help improve performance.</p>
#             </div>
#         </body>
#         </html>
#         """.format(performance_data.get('detailed_analysis', 'No detailed analysis available.'))
        
#         return html
    
#     @staticmethod
#     def generate_pdf(html_content, output_path=None):
#         """Convert HTML to PDF"""
#         if output_path is None:
#             output_path = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
#         try:
#             # Try using pdfkit first (requires wkhtmltopdf)
#             pdfkit.from_string(html_content, output_path)
#             return output_path
#         except:
#             try:
#                 # Fallback to xhtml2pdf
#                 with open(output_path, "wb") as f:
#                     pisa.CreatePDF(html_content, dest=f)
#                 return output_path
#             except Exception as e:
#                 print(f"Error generating PDF: {e}")
#                 # Save as HTML instead
#                 html_path = output_path.replace('.pdf', '.html')
#                 with open(html_path, 'w', encoding='utf-8') as f:
#                     f.write(html_content)
#                 return html_path
