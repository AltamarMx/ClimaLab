from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
from utils.config import latitude, longitude


modules_pv = {
    "Longi 620W Mono": {
        "pdc0": 620,
        "gamma_pdc": -0.0028
    },
    "Canadian Solar 665W Mono PERC": {
        "pdc0": 665,
        "gamma_pdc": -0.0034
    },
    "JA Solar 605W Mono": {
        "pdc0": 605,
        "gamma_pdc": -0.0035
    },
    "Trina Solar 605W Mono": {
        "pdc0": 605,
        "gamma_pdc": -0.0034
    }
}

assembly_options = {
    "Módulo monocristalino/policristalino en rack abierto": "open_rack_glass_polymer",
    "Módulo en estructura con aislamiento": "insulated_back_glass_polymer"
}

inverters = {
    "Huawei SUN2000 480V (98.8%)": 0.988,
    "Solis GC20K 600V (98.3%)": 0.983,
    "Growatt MIN 4200TL-X2 360V (98.4%)":0.984
}

# Interfaz de usuario
pv_calc_ui = ui.page_fluid(
    ui.h2("Análisis solar fotovoltaico"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("model_pv","Selecciona un modelo de módulo FV", choices = list(modules_pv.keys()), selected = "Longi 620W Mono"),
            ui.input_select("assembly","Selecciona un modo de instalación", choices = list(assembly_options.keys()), selected = "Módulo monocristalino/policristalino en rack abierto" ),
            ui.input_select("inverter_model","Seleccione un modelo de inversor", choices = list(inverters.keys()), selected = "Huawei SUN2000 480V (98.8%)"),
            ui.input_numeric("tilt","Ángulo de inclinación del módulo (°)", value = latitude),
            ui.input_numeric("azimuth","Ángulo de azimuth del módulo (°)", value = 180),
            ui.input_task_button("run_sim_pv", "Calcular", class_="mb-4"),  
            ui.popover(
            ui.input_action_button("btn_info_azimuth", "ℹ️ Ayuda", size="sm"),
            ui.HTML('''
                    <ul>
                        <li>El ángulo de <strong>azimuth</strong> representa la orientación del módulo respecto al norte geográfico.</li>
                        <li>Un azimuth de <strong>180°</strong> indica orientación al sur; <strong>90°</strong> es el este.</li>
                        <li><strong>POA</strong> significa <em>plane-of-array</em>: el plano del módulo FV.</li>
                        <li><strong>Irradiancia POA</strong> es la irradiancia sobre un plano o módulo FV.</li>
                        <li><strong>HSP</strong> significa <em>hora solar pico</em>.</li>
                    </ul>
                '''),
            title="Información relevante",
            id="popover_info",
            placement="right"
            )                           
        ),
        ui.div(
        output_widget("graph_energy_month"),
        ),
        ui.div(
            output_widget("graph_irradiances"),
            output_widget("graph_ac_power"),
            ui.download_button("download_data_poa", "Descargar datos irradiancia POA + Potencia AC")
        ),
        ui.div(
            ui.h4("Tabla de HSP promedio mensual y anual por inclinación"),
            ui.output_table("table_hsp"),
            ui.download_button("download_table_hsp", "Descargar tabla HSP")
        ),
        ui.div(
            output_widget("graph_hsp")
        )
        
    )
)