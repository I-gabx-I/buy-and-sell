import streamlit as st
from fpdf import FPDF
import tempfile
import os
from PIL import Image
import io

# --- CONFIGURACIÓN GENERAL ---
TASA_CAMBIO = 7.95  # <--- CAMBIO SOLICITADO (ANTES 7.80)

# --- 1. GASTOS FIJOS COPART ---
GASTOS_FIJOS_COPART = {
    "Salvage (Chocado)": { "gate": 95.00, "environmental": 15.00, "title_mailing": 20.00 },
    "Clean Title (Limpio)": { "gate": 79.00, "environmental": 0.00, "title_mailing": 20.00 }
}

# --- 2. GASTOS ADMINISTRATIVOS EXTRA (USA) ---
EXTRA_USD_BL = 20.00
EXTRA_USD_PAPELERIA = 25.00
EXTRA_USD_WIRE = 50.00 
TOTAL_EXTRAS_USD = EXTRA_USD_BL + EXTRA_USD_PAPELERIA + EXTRA_USD_WIRE

# --- 3. GASTOS FIJOS GUATEMALA (TRAMITE) ---
EXTRA_GTQ_HONORARIOS = 2000.00
EXTRA_GTQ_PLACAS = 75.00
EXTRA_GTQ_CIRCULACION = 500.00
EXTRA_GTQ_TRAMITE_ADUANAL = 1750.00

# --- 4. BASES DE DATOS (LOGÍSTICA) ---
FLETES = {
    "Delaware":   {"Sedan": 875, "SUV": 925, "Medianos": 1050},
    "Florida":    {"Sedan": 870, "SUV": 925, "Medianos": 1050},
    "Texas":      {"Sedan": 875, "SUV": 1070, "Medianos": 1170},
    "California": {"Sedan": 1190, "SUV": 1380, "Medianos": 1480}
}

GRUAS = {
    "AK - Alaska": { "Anchorage - Alaska": 0 },
    "AL - Alabama": { "Birmingham - Copart - IAA": 500, "Dothan - Copart - IAA": 475, "Huntsville - IAA": 500, "Mobile Copart": 450, "Montgomery Copart": 450, "Tanner Copart": 500 },
    "AR - Arkansas": { "Fayetteville Copart - IAA": 475, "Little Rock Copart - IAA": 400 },
    "AZ - Arizona": { "Phoenix Copart": 325, "Phoenix North Copart": 425, "Tucson Copart - IAA": 425 },
    "CA - California": {
        "Ace Perris IAA": 300, "Ace Carson IAA": 150, "Adelanto Copart": 300, "Anaheim IAA": 175, "Antelope Copart": 350, "Bakersfield Copart": 250,
        "Colton": 200, "East Bay IAA": 370, "Fontana IAA": 200, "Fontana Riverside IAA": 385, "Fontana San Bernardino IAA": 0, "Fremont IAA": 370, "Fresno Copart - IAA": 300, "Hayward Copart": 370, "High Desert IAA": 250, "Long Beach Copart": 250, "Los Ángeles Copart": 150, "Los Ángeles Perris Copart": 0, "Los Ángeles IAA": 150, "Los Ángeles South IAA": 150, "Martínez Copart": 370, "North Hollywood IAA": 225, "North Hollywood Burbank IAA": 0, "Rancho Cucamonga Copart": 200, "Rancho Cucamonga - Perris Copart": 0, "Redding Copart": 0, "San Bernardino Copart": 175, "Sacramento Copart - IAA": 350, "Sacramento - Modesto Copart": 425, "San Diego Copart - IAA": 225, "San Diego - La Media": 0, "San José Copart": 370, "Santa Clarita": 325, "Stockton": 500, "Sun Valley": 200, "Vallejo Copart": 370, "Vallejo - Green Canyon Copart": 450, "Van Nuys Copart": 200, "Van Nuys - Lancaster Copart": 0, "Van Nuys - Sun Valley Copart": 0, "Van Nuys - Santa Paula": 250, "Van Nuys - Santa Paula Santa Copart": 0, "Van Nuys - Santa Paula Copart": 300
    },
    "CO - Colorado": { "Denver Copart - IAA": 640, "Denver East IAA": 640, "Colorado Spring Copart": 0, "Webster Colorado IAA": 0 },
    "FL - Florida": {
        "Clearwater IAA": 220, "Clewiston Sublot Copart": 225, "Jefferson Sublot": 525, "Sublot Thonotosassa": 275, "Ft. Myers IAA": 220, "Ft. Piece Copart - IAA": 150, "Jacksonville IAA": 270, "Jacksonville East & West Copart - IAA": 270, "Jacksonville St. Augustine": 290, "Miami Central Copart": 100, "Miami North - Copart - IAA": 100, "Miami North - Pembroke Pines IAA": 130, "Miami South - Copart - IAA": 100, "Ocala Copart": 275, "Orlando - Copart - IAA": 200, "Orlando North & South - Copart - IAA": 200, "Orlando IAA - Sublot Boggy Greek": 225, "Orlando - Manheim": 210, "Pensacola IAA": 350, "Pensacola - Sublot Defuniak": 415, "Punta Gorda Copart": 220, "Punta Gorda South Copart": 250, "Sublot Okeechobee": 225, "Tallahassee Copart": 320, "Tampa IAA": 220, "Tampa US41 IAA": 250, "Tampa North IAA": 225, "Tampa South Copart": 200, "Tampa South Dover Copart": 265, "Tampa South Mulberry Copart": 270, "West Palm Beach Copart": 120, "West Palm Beach IAA": 145, "Ft. Laudardale - Manheim": 75
    },
    "GA - Georgia": { "Atlanta CrashedToys Copart": 370, "Atlanta East & West - Copart - IAA": 370, "Atlanta IAA": 370, "Atlanta North & South - Copart - IAA": 370, "Atlanta West Farbum": 375, "Atlanta - Manheim": 375, "Augusta Copart": 400, "Cartersville Copart": 370, "Fairburn Copart": 375, "Macon - Copart - IAA": 365, "Savannah Copart - IAA": 315, "Savannah Vertia Sublot - GA": 425, "Tifton Copart - IAA": 365 },
    "IA - Iowa": { "Davenport Copart - IAA": 0, "Des Moines Copart - IAA": 0, "Elbridge Copart": 0 },
    "ID - Idaho": { "Boise Copart - IAA": 0 },
    "IL - Illinois": { "Chicago North Copart - IAA": 675, "Chicago South / Heights Copart": 675, "Chicago South IAA": 675, "Chicago Blue Island": 675, "Chicago - Manheim": 650, "Lincoln IAA": 0, "Peoria IAA": 0, "Southern Illinois Copart": 675, "ST. Louis IAA": 675, "Wheeling Copart": 0, "Manheim Arena Illinois": 650 },
    "IN - Indiana": { "Cicero Copart": 700, "Fort Wayne Copart": 0, "Hammond Copart": 650, "Indianapolis Copart - IAA": 625, "Indianapolis South IAA": 650, "South Bend IAA": 0, "Dyer Copart": 725 },
    "KS - Kansas": { "Kansas City Copart - IAA": 570, "Kansas City East Copart": 570, "Wichita Copart - IAA": 525 },
    "KY - Kentucky": { "Ashland IAA": 0, "Bowling Green IAA": 0, "Earling Copart": 0, "Lexington East & West Copart": 625, "Louisville Copart - IAA": 625, "Louisville North IAA": 700, "Paducah": 0, "Walton Copart": 675 },
    "LA - Louisiana": { "Baton Rouge Copart - IAA": 320, "Lafayette Copart - IAA": 250, "New Orleans Copart - IAA": 325, "New Orleans East Copart - IAA": 325, "Shreveport Copart - IAA": 275 },
    "MI - Michigan": { "Detroit IAA": 0, "Grand Rapids IAA": 0, "Flint Copart - IAA": 0, "Lansing IAA": 0 },
    "MN - Minnesota": { "Minneapolis Copart": 970, "Minneapolis Bunker Copart": 1070, "Minneapolis Faribault Copart": 1070, "Minneapolis Fridley Copart": 1070, "Minneapolis Rice IAA": 1070, "Minneapolis Roseville IAA": 1070, "Minneapolis South IAA": 970, "Minneapolis North Copart": 970, "Minneapolis - ST. Paul IAA": 970, "ST. Cloud Copart": 970 },
    "MO - Missouri": { "Kansas City East IAA": 0, "St. Louis Copart - IAA": 625, "Springfield Copart - IAA": 630, "Springfield Sublot Copart - IAA": 675, "Sikeston Copart - IAA": 630, "Columbia Copart - IAA": 0 },
    "MS - Mississippi": { "Jackson Copart - IAA": 525, "Gulf Coast IAA": 475, "Grenada IAA": 500 },
    "MT - Montana": { "Missoula IAA": 0, "Helena Copart": 0 },
    "NC - North Carolina": { "Asheville IAA": 525, "Charlotte IAA": 400, "Charlotte Holding Offsite": 475, "China Grove Copart - IAA": 400, "Concord Copart - IAA": 400, "Gastonia": 425, "Greensboro IAA": 400, "Lumberton Copart": 400, "Mebane Copart": 400, "Mocksville Copart": 400, "Raleigh Copart - IAA": 400, "Raleigh North Copart": 400, "Wilmington IAA": 525, "High Point IAA": 475 },
    "ND - North Dakota": { "Fargo IAA": 0 },
    "NE - Nebraska": { "Lincoln Copart": 0, "Omaha Copart": 0 },
    "NM - New Mexico": { "Albuquerque Copart - IAA": 570 },
    "NV - Nevada": { "Las Vegas Copart - IAA": 325, "Las Vegas - Clayton Copart": 325, "Las Vegas - Hammer Copart": 325, "Las Vegas - Sublot Lucky": 425, "Las Vegas West / East": 325, "Reno Copart - IAA": 550 },
    "OH - Ohio": { "Akron Canton IAA": 725, "Akron Copart": 725, "Cincinnati IAA": 725, "Cincinnati South IAA": 725, "Cleveland Copart - IAA": 725, "Cleveland East Copart": 725, "Cleveland West Copart": 725, "Cleveland - Adesa": 650, "Columbus Copart - IAA": 725, "Columbus - Statement": 825, "Dayton Copart - IAA": 725 },
    "OK - Oklahoma": { "Oklahoma City Copart - IAA": 450, "Oklahoma Copart - Sublot Moore": 475, "Tulsa Copart - IAA": 415 },
    "OR - Oregon": { "Portland IAA": 595, "Portland North Copart": 595, "Portland South Copart": 595, "Portland West IAA": 595, "Eugene Copart - IAA": 595 },
    "SC - South Carolina": { "Charleston IAA": 350, "Columbia Copart - IAA": 350, "Columbia Copart - IAA SC Sublot Gaston": 350, "Columbia Copart - Sublot Gaston": 375, "Columbia Copart - Sublot South Gaston": 375, "Columbia Copart - Sublot Sha Liu": 375, "Greenville IAA": 375, "Lexington IAA": 350, "North Charleston Copart": 350, "Spartanburg Copart": 375, "Greer - Manheim": 380 },
    "SD - South Dakota": { "Sioux Falls": 0 },
    "TN - Tennessee": { "Chattanooga IAA": 550, "Knoxville Copart - IAA": 500, "Memphis Copart - IAA": 550, "Nashville Copart - IAA": 500 },
    "TX - Texas": {
        "Abilene Copart - IAA": 330, "Amarillo Copart - IAA": 420, "Andrews Copart - IAA": 460, "Austin Copart - IAA": 240, "Austin Sublot North": 325, "Corpus Christi Copart - IAA": 250, "Dallas Copart - IAA": 250, "Dallas South Copart - IAA": 250, "El Paso Copart - IAA": 430, "Dallas Ft. Worth Copart - IAA": 250, "Fort Worth Copart": 270, "Fort Worth North IAA": 270, "Houston Copart IAA": 150, "Houston South North & West Copart - IAA": 180, "Houston East Copart - IAA": 180, "Longview Copart - IAA": 250, "Lubbock Copart - IAA": 425, "Lufkin Copart - IAA": 250, "McAllen Copart - IAA": 300, "Permian Basin Copart - IAA": 420, "San Antonio Copart": 240, "San Antonio South IAA": 240, "Waco Copart - IAA": 270, "Sublot Taylor": 370
    },
    "UT - Utah": { "Salt Lake City Copart - IAA": 400, "Ogden Copart": 400 },
    "WA - Washington": { "Graham Copart": 725, "Paso Copart": 825, "Seattle IAA": 725, "Spokane Copart - IAA": 825, "Tacoma": 0 }
}

MAPA_ESTADOS_PUERTOS = {
    # Región OESTE -> CALIFORNIA
    "AK - Alaska": "California", "AZ - Arizona": "California", "CA - California": "California",
    "ID - Idaho": "California", "MT - Montana": "California", "NV - Nevada": "California", 
    "OR - Oregon": "California", "UT - Utah": "California", "WA - Washington": "California",
    
    # Región SUR/CENTRO -> TEXAS
    "AR - Arkansas": "Texas", "CO - Colorado": "Texas", "KS - Kansas": "Texas",
    "LA - Louisiana": "Texas", "MO - Missouri": "Texas", "NE - Nebraska": "Texas",
    "NM - New Mexico": "Texas", "OK - Oklahoma": "Texas", "TX - Texas": "Texas",
    
    # Región ESTE/SUR -> FLORIDA
    "AL - Alabama": "Florida", "FL - Florida": "Florida", "GA - Georgia": "Florida",
    "IA - Iowa": "Florida", "IL - Illinois": "Florida", "IN - Indiana": "Florida",
    "KY - Kentucky": "Florida", "MI - Michigan": "Florida", "MN - Minnesota": "Florida",
    "MS - Mississippi": "Florida", "NC - North Carolina": "Florida", "ND - North Dakota": "Florida",
    "OH - Ohio": "Florida", "SC - South Carolina": "Florida", "SD - South Dakota": "Florida",
    "TN - Tennessee": "Florida"
}

# --- FUNCIONES DE CÁLCULO ---
def get_virtual_fee_salvage(precio, es_live):
    if precio < 100: return 0
    if es_live:
        if precio < 500: return 50
        elif precio < 1000: return 65
        elif precio < 1500: return 85
        elif precio < 2000: return 95
        elif precio < 4000: return 110
        elif precio < 6000: return 125
        elif precio < 8000: return 145
        else: return 160
    else:
        if precio < 500: return 40
        elif precio < 1000: return 55
        elif precio < 1500: return 75
        elif precio < 2000: return 85
        elif precio < 4000: return 100
        elif precio < 6000: return 110
        elif precio < 8000: return 125
        else: return 140

def get_virtual_fee_clean(precio, es_live):
    if precio < 100: return 0
    if es_live:
        if precio < 500: return 49
        elif precio < 1000: return 59
        elif precio < 1500: return 79
        elif precio < 2000: return 89
        elif precio < 4000: return 99
        elif precio < 6000: return 109
        elif precio < 8000: return 139
        else: return 149
    else:
        if precio < 500: return 39
        elif precio < 1000: return 49
        elif precio < 1500: return 69
        elif precio < 2000: return 79
        elif precio < 4000: return 89
        elif precio < 6000: return 99
        elif precio < 8000: return 119
        else: return 129

def get_buyer_fee_salvage(precio):
    if precio < 50: return 27.50
    elif precio < 100: return 50.00
    elif precio < 200: return 90.00
    elif precio < 300: return 145.00
    elif precio < 350: return 155.00
    elif precio < 400: return 167.50
    elif precio < 450: return 200.00
    elif precio < 500: return 210.00
    elif precio < 550: return 235.00
    elif precio < 600: return 240.00
    elif precio < 700: return 275.00
    elif precio < 800: return 312.50
    elif precio < 900: return 342.50
    elif precio < 1000: return 370.00
    elif precio < 1200: return 440.00
    elif precio < 1300: return 460.00
    elif precio < 1400: return 482.50
    elif precio < 1500: return 510.00
    elif precio < 1600: return 530.00
    elif precio < 1700: return 555.00
    elif precio < 1800: return 582.50
    elif precio < 2000: return 620.00
    elif precio < 2400: return 662.50
    elif precio < 2500: return 705.00
    elif precio < 3000: return 775.00
    elif precio < 3500: return 830.00
    elif precio < 4000: return 927.50
    elif precio < 4500: return 935.00
    elif precio < 5000: return 1000.00
    elif precio < 5500: return 1025.00
    elif precio < 6000: return 1055.00
    elif precio < 6500: return 1085.00
    elif precio < 7000: return 1110.00
    elif precio < 7500: return 1145.00
    elif precio < 8000: return 1175.00
    elif precio < 8500: return 1200.00
    elif precio < 9000: return 1225.00
    elif precio < 10000: return 1225.00
    else: return 1225.00 + ((precio - 10000) * 0.20)

def get_buyer_fee_clean(precio):
    if precio < 50: return 27.50
    elif precio < 100: return 50.00
    elif precio < 200: return 90.00
    elif precio < 300: return 135.00
    elif precio < 350: return 137.50
    elif precio < 400: return 140.00
    elif precio < 450: return 182.50
    elif precio < 500: return 185.00
    elif precio < 550: return 212.50
    elif precio < 600: return 215.00
    elif precio < 700: return 245.00
    elif precio < 800: return 270.00
    elif precio < 900: return 295.00
    elif precio < 1000: return 325.00
    elif precio < 1200: return 385.00
    elif precio < 1300: return 415.00
    elif precio < 1400: return 435.00
    elif precio < 1500: return 455.00
    elif precio < 1600: return 470.00
    elif precio < 1700: return 495.00
    elif precio < 1800: return 510.00
    elif precio < 2000: return 540.00
    elif precio < 2400: return 590.00
    elif precio < 2500: return 605.00
    elif precio < 3000: return 650.00
    elif precio < 3500: return 775.00
    elif precio < 4000: return 875.00
    elif precio < 4500: return 935.00
    elif precio < 6000: return 1000.00
    elif precio < 7500: return 1050.00
    elif precio < 8000: return 1065.00
    elif precio < 10000: return 1090.00
    else: return 1090.00 + ((precio - 10000) * 0.20)

# --- FUNCIÓN GENERAR PDF DETALLADO (V7 - DOBLE MONEDA + SUBTOTALES) ---
def generar_pdf_detallado(datos_pdf, imagen_file):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False) # CONTROL MANUAL DE SALTO DE PÁGINA
    pdf.add_page()
    
    # --- ENCABEZADO ---
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, txt="Cotización de Importación", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, txt="Generado automáticamente por Importadora App", ln=True, align="C")
    pdf.ln(10)
    
    # --- 1. INFORMACIÓN DEL VEHÍCULO ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="1. INFORMACIÓN DEL VEHÍCULO", ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 11)
    vehiculo = datos_pdf['vehiculo']
    pdf.cell(95, 7, txt=f"Lote: {vehiculo['lote']}", border=1)
    pdf.cell(95, 7, txt=f"Vehículo: {vehiculo['descripcion']}", border=1, ln=True)
    pdf.cell(95, 7, txt=f"Tipo Título: {vehiculo['titulo']}", border=1)
    pdf.cell(95, 7, txt=f"Ubicación: {vehiculo['ubicacion']}", border=1, ln=True)
    pdf.ln(5)

    # --- FOTO GIGANTE DEL AUTO ---
    if imagen_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(imagen_file.getvalue())
                tmp_path = tmp_file.name
            
            ancho_imagen = 170
            x_img = (210 - ancho_imagen) / 2
            
            # Verificar espacio para foto (aprox 100mm altura)
            if pdf.get_y() + 100 > 270:
                pdf.add_page()

            pdf.image(tmp_path, x=x_img, w=ancho_imagen)
            os.remove(tmp_path)
            pdf.ln(5)
        except:
            pdf.cell(0, 10, txt="(Error al cargar imagen)", ln=True, align="C")

    # --- 2. DESGLOSE DE COSTOS ---
    if pdf.get_y() + 20 > 270: pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="2. DESGLOSE DE COSTOS", ln=True, fill=True)
    pdf.ln(2)
    
    def fila(texto, valor, negrita=False, subitem=False):
        # CHECK DE PAGINACIÓN MANUAL PARA EVITAR BUG DE TABLAS CORTADAS
        if pdf.get_y() > 265: # Si estamos muy abajo (A4 es ~297mm)
            pdf.add_page()
            
        pdf.set_font("Arial", "B" if negrita else "", 10)
        indent = "    " if subitem else ""
        pdf.cell(130, 6, txt=indent + texto, border="B") # Reducido un poco para dar espacio a valores largos
        pdf.cell(60, 6, txt=valor, border="B", align="R", ln=True)

    fin = datos_pdf['financiero']
    det_copart = datos_pdf['detalle_copart']
    det_usa = datos_pdf['detalle_usa']
    det_gt = datos_pdf['detalle_gt']
    
    # A. Copart
    if pdf.get_y() + 10 > 270: pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="A. Costos Copart (USA)", ln=True)
    fila("Precio Subasta (Winning Bid)", fin['precio_subasta'], negrita=True)
    fila("   - Buyer Fee", det_copart['buyer'], subitem=True)
    fila("   - Virtual Bid Fee", det_copart['virtual'], subitem=True)
    fila("   - Gate Fee", det_copart['gate'], subitem=True)
    fila("   - Environmental Fee", det_copart['env'], subitem=True)
    fila("   - Title Mailing", det_copart['title'], subitem=True)
    fila("TOTAL FACTURA COPART", fin['total_copart'], negrita=True)
    pdf.ln(2)

    # B. Logística
    if pdf.get_y() + 10 > 270: pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="B. Logística y Trámites", ln=True)
    fila("Grúa (Towing) -> Puerto", fin['grua'])
    fila("Flete Marítimo (Ocean Freight)", fin['barco'])
    fila("   - BL (Documentación Naviera)", det_usa['bl'], subitem=True)
    fila("   - Papelería / Courier", det_usa['papeleria'], subitem=True)
    fila("   - Wire Transfer (Transferencia)", det_usa['wire'], subitem=True)
    fila("TOTAL LOGÍSTICA", fin['total_logistica'], negrita=True)
    pdf.ln(2)

    # C. Impuestos
    if pdf.get_y() + 10 > 270: pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="C. Impuestos y Locales (GT)", ln=True)
    fila("Impuestos Aduana (IPRIMA + IVA)", fin['impuestos_gtq'])
    fila("Trámite Aduanal", fin['tramite_aduanal'])
    fila("   - Honorarios de Importación", det_gt['honorarios'], subitem=True)
    fila("   - Placas y Tarjeta", det_gt['placas'], subitem=True)
    fila("   - Impuesto de Circulación", det_gt['circulacion'], subitem=True)
    if fin['flete_interno'] != "No incluido":
        fila("Flete Interno (Puerto -> Capital)", fin['flete_interno'])
    fila("TOTAL GASTOS LOCALES", fin['total_locales'], negrita=True)
    pdf.ln(2)

    # --- 3. REPARACIONES Y REPUESTOS ---
    lista_rep = datos_pdf.get('lista_repuestos', [])
    lista_mo = datos_pdf.get('lista_mano_obra', [])
    subtotal_rep = datos_pdf.get('subtotal_repuestos', "Q0.00")
    subtotal_mo = datos_pdf.get('subtotal_mano_obra', "Q0.00")
    
    if lista_rep or lista_mo:
        pdf.ln(5)
        if pdf.get_y() + 20 > 270: pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, txt="3. REPARACIONES Y SERVICIOS", ln=True, fill=True)
        pdf.ln(2)
        
        # TABLA DE REPUESTOS
        if lista_rep:
            if pdf.get_y() + 10 > 270: pdf.add_page()
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, "A. REPUESTOS COTIZADOS", ln=True)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(90, 6, "Repuesto", 1)
            pdf.cell(30, 6, "Precio (Q)", 1)
            pdf.cell(70, 6, "Ref/Link", 1, ln=True)
            
            pdf.set_font("Arial", "", 9)
            for rep in lista_rep:
                # Altura de la fila
                altura_fila = 15 if rep.get('foto_bytes') else 8
                
                # PROTECCIÓN DE SALTO DE PÁGINA
                if pdf.get_y() + altura_fila > 270:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(90, 6, "Repuesto (cont.)", 1)
                    pdf.cell(30, 6, "Precio (Q)", 1)
                    pdf.cell(70, 6, "Ref/Link", 1, ln=True)
                    pdf.set_font("Arial", "", 9)

                y_inicio = pdf.get_y()
                
                # Nombre
                nombre_corto = (rep['nombre'][:35] + '..') if len(rep['nombre']) > 35 else rep['nombre']
                pdf.set_xy(10, y_inicio)
                pdf.cell(90, altura_fila, nombre_corto, 1)
                
                # Miniatura
                if rep.get('foto_bytes'):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_th:
                            tmp_th.write(rep['foto_bytes'])
                            tmp_th_path = tmp_th.name
                        pdf.image(tmp_th_path, x=60, y=y_inicio+1, h=13)
                        os.remove(tmp_th_path)
                    except: pass
                
                # Precio
                pdf.set_xy(100, y_inicio)
                pdf.cell(30, altura_fila, f"Q{rep['precio']:,.2f}", 1)
                
                # Link
                pdf.set_xy(130, y_inicio)
                link_corto = (rep['link'][:35] + '..') if len(rep['link']) > 35 else rep['link']
                pdf.cell(70, altura_fila, link_corto, 1, ln=True)
            
            # Subtotal Repuestos
            pdf.set_font("Arial", "B", 9)
            pdf.cell(140, 6, "Subtotal Repuestos:", 0, 0, 'R')
            pdf.cell(50, 6, subtotal_rep, 0, 1, 'R')
        
        # TABLA DE MANO DE OBRA
        if lista_mo:
            pdf.ln(5)
            if pdf.get_y() + 20 > 270: pdf.add_page()
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, "B. MANO DE OBRA Y SERVICIOS", ln=True)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(140, 6, "Servicio / Descripción", 1)
            pdf.cell(50, 6, "Precio (Q)", 1, ln=True)
            
            pdf.set_font("Arial", "", 9)
            for mo in lista_mo:
                if pdf.get_y() + 8 > 270: pdf.add_page()
                pdf.cell(140, 6, mo['descripcion'], 1)
                pdf.cell(50, 6, f"Q{mo['precio']:,.2f}", 1, ln=True)
            
            # Subtotal Mano de Obra
            pdf.set_font("Arial", "B", 9)
            pdf.cell(140, 6, "Subtotal Mano de Obra:", 0, 0, 'R')
            pdf.cell(50, 6, subtotal_mo, 0, 1, 'R')
        
        # TOTAL REPARACIONES
        pdf.ln(2)
        if pdf.get_y() + 10 > 270: pdf.add_page()
        fila("TOTAL REPARACIONES Y SERVICIOS", fin['total_reparaciones'], negrita=True)

    # --- 4. GRAN TOTAL FINAL ---
    pdf.ln(10)
    if pdf.get_y() + 20 > 270: pdf.add_page() # Asegurar que el total no quede cortado
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(140, 15, txt=" INVERSIÓN TOTAL PROYECTO (Q)", fill=True)
    pdf.cell(50, 15, txt=fin['gran_total'] + " ", fill=True, align="R", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- INICIALIZAR ESTADO ---
if 'repuestos' not in st.session_state:
    st.session_state['repuestos'] = []
if 'mano_obra_lista' not in st.session_state:
    st.session_state['mano_obra_lista'] = []

# --- INTERFAZ GRÁFICA ---
st.title("🚗 Importadora - Cotizador V7")

# 1. DATOS DEL CARRO
st.header("1. Datos del Vehículo")
col_lote, col_car1 = st.columns([1, 2])
with col_lote:
    lote = st.text_input("Lote / Stock #", placeholder="Ej. 543210")
with col_car1:
    col_m, col_mod, col_a = st.columns(3)
    marca = col_m.text_input("Marca", placeholder="Toyota")
    modelo = col_mod.text_input("Modelo", placeholder="Corolla")
    anio = col_a.text_input("Año", placeholder="2020")
foto_carro = st.file_uploader("Subir Foto del Auto", type=["jpg", "png", "jpeg"])

# 2. COMPRA Y SUBASTA
st.header("2. Detalles de Compra")
c1, c2 = st.columns(2)
with c1:
    precio_subasta = st.number_input("Precio Subasta ($)", min_value=0.0, step=100.0)
    tipo_titulo = st.radio("Título:", ["Salvage (Chocado)", "Clean Title (Limpio)"])
with c2:
    tipo_compra = st.radio("Compra:", ["Subasta en Vivo (Live)", "Pre-Oferta / Buy It Now"])
    tipo_vehiculo = st.radio("Tamaño:", ["Sedan", "SUV", "Medianos"])
es_live = True if "Live" in tipo_compra else False

# 3. UBICACIÓN
st.header("3. Ubicación Logística")
estado_user = st.selectbox("Estado:", sorted(list(GRUAS.keys())))
patio_user = st.selectbox("Patio/Ciudad:", sorted(list(GRUAS[estado_user].keys())))
precio_grua = GRUAS[estado_user][patio_user]

# 4. GESTOR DE REPUESTOS Y MANO DE OBRA (NUEVO)
st.header("4. Reparaciones y Repuestos")

# TABS PARA ORGANIZAR MEJOR
tab1, tab2 = st.tabs(["🔩 Repuestos", "🛠️ Mano de Obra"])

with tab1:
    st.write("Agrega aquí los repuestos cotizados:")
    with st.form("form_repuesto", clear_on_submit=True):
        c_rep1, c_rep2 = st.columns([2, 1])
        with c_rep1:
            nom_rep = st.text_input("Nombre Repuesto", placeholder="Ej. Radiador")
            link_rep = st.text_input("Link / Tienda", placeholder="Ej. FPK / Moauto")
        with c_rep2:
            prec_rep = st.number_input("Precio (Q)", min_value=0.0, step=50.0)
            foto_rep = st.file_uploader("Foto Miniatura", type=["jpg", "png"])
        
        if st.form_submit_button("➕ Agregar Repuesto"):
            if nom_rep and prec_rep > 0:
                foto_bytes = foto_rep.getvalue() if foto_rep else None
                st.session_state['repuestos'].append({
                    "nombre": nom_rep, "precio": prec_rep, "link": link_rep, "foto_bytes": foto_bytes
                })
                st.rerun()

    if st.session_state['repuestos']:
        st.write("**Listado:**")
        total_rep = 0
        for i, r in enumerate(st.session_state['repuestos']):
            c_lst1, c_lst2, c_lst3 = st.columns([3, 1, 1])
            icon = "📸" if r['foto_bytes'] else ""
            c_lst1.text(f"{icon} {r['nombre']} ({r['link']})")
            c_lst2.text(f"Q{r['precio']:,.2f}")
            if c_lst3.button("❌", key=f"del_rep_{i}"):
                st.session_state['repuestos'].pop(i)
                st.rerun()
            total_rep += r['precio']
        st.info(f"Subtotal Repuestos: Q{total_rep:,.2f}")

with tab2:
    st.write("Agrega servicios de mano de obra:")
    with st.form("form_mo", clear_on_submit=True):
        c_mo1, c_mo2 = st.columns([2, 1])
        with c_mo1:
            desc_mo = st.text_input("Descripción Servicio", placeholder="Ej. Pintura General")
        with c_mo2:
            prec_mo = st.number_input("Costo Estimado (Q)", min_value=0.0, step=100.0)
        
        if st.form_submit_button("➕ Agregar Mano de Obra"):
            if desc_mo and prec_mo > 0:
                st.session_state['mano_obra_lista'].append({"descripcion": desc_mo, "precio": prec_mo})
                st.rerun()

    if st.session_state['mano_obra_lista']:
        st.write("**Listado:**")
        total_mo = 0
        for i, m in enumerate(st.session_state['mano_obra_lista']):
            c_lst1, c_lst2, c_lst3 = st.columns([3, 1, 1])
            c_lst1.text(m['descripcion'])
            c_lst2.text(f"Q{m['precio']:,.2f}")
            if c_lst3.button("❌", key=f"del_mo_{i}"):
                st.session_state['mano_obra_lista'].pop(i)
                st.rerun()
            total_mo += m['precio']
        st.info(f"Subtotal Mano de Obra: Q{total_mo:,.2f}")

# Calcular totales de reparación
sum_repuestos = sum(r['precio'] for r in st.session_state['repuestos'])
sum_mano_obra = sum(m['precio'] for m in st.session_state['mano_obra_lista'])
total_reparaciones_q = sum_repuestos + sum_mano_obra

# 5. OPCIONES ADICIONALES
st.write("---")
usar_flete_gt = st.checkbox("Incluir Flete Interno (Puerto -> Capital) (+Q900)", value=True)

# BOTÓN PRINCIPAL
if st.button("CALCULAR PRESUPUESTO FINAL 🚀", use_container_width=True):
    st.divider()
    
    # --- CÁLCULOS ---
    puerto = MAPA_ESTADOS_PUERTOS.get(estado_user, "Florida")
    costo_barco = FLETES.get(puerto, {}).get(tipo_vehiculo, 0)
    
    conf_fijos = GASTOS_FIJOS_COPART[tipo_titulo]
    gate = conf_fijos["gate"]
    env = conf_fijos["environmental"]
    title = conf_fijos["title_mailing"]
    gate_env_total = gate + env + title
    
    if tipo_titulo == "Salvage (Chocado)":
        virtual = get_virtual_fee_salvage(precio_subasta, es_live)
        buyer = get_buyer_fee_salvage(precio_subasta)
    else:
        virtual = get_virtual_fee_clean(precio_subasta, es_live)
        buyer = get_buyer_fee_clean(precio_subasta)
    
    total_copart = gate_env_total + virtual + buyer
    base_imponible_usd = precio_subasta + total_copart
    impuestos_usd = base_imponible_usd * 0.32
    impuestos_gtq = impuestos_usd * TASA_CAMBIO
    total_logistica_usd = precio_grua + costo_barco + TOTAL_EXTRAS_USD
    
    gasto_local_base = EXTRA_GTQ_HONORARIOS + EXTRA_GTQ_PLACAS + EXTRA_GTQ_CIRCULACION
    gasto_local_total = gasto_local_base + EXTRA_GTQ_TRAMITE_ADUANAL
    if usar_flete_gt: gasto_local_total += 900
    
    gran_total_usd = base_imponible_usd + impuestos_usd + total_logistica_usd
    total_final_quetzales = (gran_total_usd * TASA_CAMBIO) + gasto_local_total
    total_con_reparacion = total_final_quetzales + total_reparaciones_q
    
    # --- VISUALIZACIÓN EN PANTALLA ---
    st.subheader("📊 Análisis de Costos")
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.markdown("### 1. Copart (USA)")
        st.write(f"Subasta: ${precio_subasta:,.2f}")
        st.write(f"Buyer Fee: ${buyer:,.2f}")
        st.markdown(f"**Total Copart: ${base_imponible_usd:,.2f}**")
        st.caption("Base para impuestos")
        st.markdown("### 3. Impuestos (SAT)")
        st.metric("Total (32%)", f"Q{impuestos_gtq:,.2f}", f"${impuestos_usd:,.2f}")

    with col_der:
        st.markdown("### 2. Logística")
        st.write(f"🚛 Grúa: ${precio_grua:,.2f}")
        st.write(f"🚢 Barco: ${costo_barco:,.2f}")
        st.write(f"📄 Docs+Wire: ${TOTAL_EXTRAS_USD:,.2f}")
        st.markdown(f"**Total Logística: ${total_logistica_usd:,.2f}**")
        st.markdown("### 4. Locales (GT)")
        st.write(f"Trámites/Aduana: Q{gasto_local_total:,.2f}")

    st.divider()
    c_tot1, c_tot2 = st.columns([2, 1])
    with c_tot1:
        st.markdown("### 🏁 TOTAL PROYECTO")
        st.success(f"Q{total_final_quetzales:,.2f} (Importación)")
        if total_reparaciones_q > 0:
            st.metric("Total con Reparaciones", f"Q{total_con_reparacion:,.2f}", f"+ Q{total_reparaciones_q:,.2f}")
    
    # --- BOTÓN PDF ---
    with c_tot2:
        st.write("") 
        
        # Helper para formato doble moneda
        def fmt_dual(val_usd):
            return f"${val_usd:,.2f} (Q{val_usd * TASA_CAMBIO:,.2f})"

        datos_pdf_completo = {
            'vehiculo': {
                'lote': lote if lote else "---",
                'descripcion': f"{marca} {modelo} {anio}",
                'titulo': tipo_titulo,
                'ubicacion': f"{patio_user}, {estado_user}"
            },
            'financiero': {
                # AHORA CON DOBLE MONEDA EN SECCIONES DE USA
                'precio_subasta': fmt_dual(precio_subasta),
                'total_copart': fmt_dual(base_imponible_usd),
                'total_logistica': fmt_dual(total_logistica_usd),
                
                # Lo de GT se queda en Q
                'impuestos_gtq': f"Q{impuestos_gtq:,.2f} (${impuestos_usd:,.2f})",
                'tramite_aduanal': f"Q{EXTRA_GTQ_TRAMITE_ADUANAL:,.2f}",
                'flete_interno': f"Q900.00" if usar_flete_gt else "No incluido",
                'total_locales': f"Q{gasto_local_total:,.2f}",
                'total_reparaciones': f"Q{total_reparaciones_q:,.2f}",
                'gran_total': f"Q{total_con_reparacion:,.2f}",
                
                # Detalle USA para tabla (Doble moneda)
                'grua': fmt_dual(precio_grua),
                'barco': fmt_dual(costo_barco),
                'extras_usa': fmt_dual(TOTAL_EXTRAS_USD),
            },
            # Detalle Atómico para el PDF (Doble moneda)
            'detalle_copart': {
                'buyer': fmt_dual(buyer),
                'virtual': fmt_dual(virtual),
                'gate': fmt_dual(gate),
                'env': fmt_dual(env),
                'title': fmt_dual(title),
            },
            'detalle_usa': {
                'bl': fmt_dual(EXTRA_USD_BL),
                'papeleria': fmt_dual(EXTRA_USD_PAPELERIA),
                'wire': fmt_dual(EXTRA_USD_WIRE),
            },
            'detalle_gt': {
                'honorarios': f"Q{EXTRA_GTQ_HONORARIOS:,.2f}",
                'placas': f"Q{EXTRA_GTQ_PLACAS:,.2f}",
                'circulacion': f"Q{EXTRA_GTQ_CIRCULACION:,.2f}",
            },
            'lista_repuestos': st.session_state['repuestos'],
            'lista_mano_obra': st.session_state['mano_obra_lista'],
            'subtotal_repuestos': f"Q{sum_repuestos:,.2f}",
            'subtotal_mano_obra': f"Q{sum_mano_obra:,.2f}"
        }
        
        pdf_bytes = generar_pdf_detallado(datos_pdf_completo, foto_carro)
        
        st.download_button(
            label="📄 Descargar PDF Detallado",
            data=pdf_bytes,
            file_name=f"Cotizacion_{lote if lote else 'V7'}.pdf",
            mime="application/pdf"
        )
