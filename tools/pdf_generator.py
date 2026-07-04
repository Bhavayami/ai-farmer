import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from logger import logger

class PDFReportGenerator:
    """
    Service for generating downloadable PDF advisory reports for farmers.
    """
    
    @staticmethod
    def generate_report(
        filename: str,
        farmer_name: str,
        region: str,
        crop_plan: str,
        weather_summary: str,
        soil_analysis: str,
        pest_disease_advisory: str,
        financial_plan: str,
        gov_schemes: str,
        action_plan: str
    ) -> str:
        """
        Creates a structured, styled PDF report at the specified filename path.
        Returns the absolute filepath.
        """
        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=54,
                leftMargin=54,
                topMargin=54,
                bottomMargin=54
            )
            
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=24,
                leading=28,
                textColor=colors.HexColor('#1E3D2F'), # Dark Forest Green
                spaceAfter=15
            )
            
            subtitle_style = ParagraphStyle(
                'ReportSubtitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                leading=14,
                textColor=colors.HexColor('#555555'),
                spaceAfter=25
            )
            
            section_heading = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#2E6F40'), # Medium Green
                spaceBefore=12,
                spaceAfter=6,
                keepWithNext=True
            )
            
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['BodyText'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=10
            )

            story = []
            
            # Header block
            story.append(Paragraph("AI Farmer Assistant - Advisory Report", title_style))
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Prepared for: <b>{farmer_name}</b> ({region})",
                subtitle_style
            ))
            
            # Metadata Table
            data = [
                [Paragraph("<b>Farmer Profile</b>", body_style), Paragraph("<b>Farm Attributes</b>", body_style)],
                [Paragraph(f"Farmer Name: {farmer_name}", body_style), Paragraph(f"Region: {region}", body_style)],
                [Paragraph(f"Primary Crops: {crop_plan.split('.')[0]}", body_style), Paragraph(f"Soil Status: See soil section below", body_style)]
            ]
            t = Table(data, colWidths=[250, 250])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F4F7F5')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D2DDD3')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#EAEAEA')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            
            # Sections
            sections = [
                ("1. Crop Planning & Agronomic Advice", crop_plan),
                ("2. Soil & Nutrient Analysis", soil_analysis),
                ("3. Weather Intelligence & Alerts", weather_summary),
                ("4. Pest & Disease Management", pest_disease_advisory),
                ("5. Market Prices & Financial Advisory", financial_plan),
                ("6. Eligible Government Schemes", gov_schemes),
                ("7. Recommended Weekly Action Plan", action_plan)
            ]
            
            for title, content in sections:
                story.append(Paragraph(title, section_heading))
                story.append(Paragraph(content.replace('\n', '<br/>'), body_style))
                story.append(Spacer(1, 10))
                
            doc.build(story)
            logger.info(f"PDF Advisory Report built successfully at {filename}")
            return os.path.abspath(filename)
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise IOError(f"PDF generation error: {e}")
