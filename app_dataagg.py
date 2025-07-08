import os
import duckdb
import io
from numpy import nan
import missingno as msno



from shiny import App, Inputs, Outputs, Session, render, ui, req, reactive
from shinywidgets import render_plotly
import faicons as fa

from utils.data_processing import load_csv, run_tests, export_data, clean_outliers
from utils.plots import plot_all_variables, plot_cleaned_radiation, plot_missingno
from utils.config import name, drop_outliers, db_name
from components.panels import panel_upload_file, panel_clean_outliers, panel_load_database, panel_admin_database
from components.helper_text import info_modal
 
  
# ui definition 
app_ui = ui.page_fluid(
    ui.page_navbar(
        ui.nav_spacer(),
        panel_upload_file(),
        panel_clean_outliers(),
        panel_load_database(),
        panel_admin_database(),
        ui.nav_control(
            ui.input_action_button(
                id="info_icon",
                label=None,
                icon=fa.icon_svg("circle-info"),
                class_=(
                    "btn "
                    "d-flex align-items-center "
                    "border-0 p-3 "
                ),
                title="Documentación"
            )
        ),
        title=name+'Admin'
    )
)


# server logic
def server(input: Inputs, output: Outputs, session: Session):
    # shared reactive storage
    rv_loaded = reactive.Value(None)
    rv_tests  = reactive.Value(None)
    rv_types   = reactive.Value(None)
    rv_plotly = reactive.Value(None)
    rv_clean = reactive.Value(None)
    rv_outliers = reactive.Value(None)
    rv_rad_plot = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.info_icon)
    def _():
        info_modal()

    # full pipeline on file upload
    @output
    @render.ui
    @reactive.event(input.file)
    async def upload_status():
        file = req(input.file())[0]["datapath"]
        total_steps = 4

        with ui.Progress(min=0, max=total_steps) as p:
            p.set(1, message="1/4 Loading file")
            df = load_csv(file)
            rv_loaded.set(df)

            p.set(2, message="2/4 Reviewing data structure")
            tests = run_tests(df)
            rv_tests.set(tests)


            p.set(3, message="3/4 Reporting columns type")
            rv_types.set(
                df.dtypes
                    .rename_axis("Column")
                    .reset_index(name="Type")
            )
            
            p.set(4, message="4/4 Plotting all data")
            # rv_types.set(plot_all_variables(df))
            # rv_plotly.set(plot_all_variables(df))
            rv_plotly.set(plot_missingno(df))

            # generate cleaned DataFrame 
            df_clean = clean_outliers(df.copy())

            # get df with ONLY outliers
            cols = ['dni_outlier', 'dhi_outlier', 'ghi_outlier']
            df_outliers = df_clean[df_clean[cols].any(axis=1)]

            # df_clean = df.copy()
            rv_clean.set(df_outliers.reset_index())
            # rv_rad_plot.set(plot_cleaned_radiation(df_clean))

            if drop_outliers:
                df_clean.loc[df_clean['dni_outlier'],  'dni'] = nan
                df_clean.loc[df_clean['dhi_outlier'],  'dhi'] = nan
                df_clean.loc[df_clean['ghi_outlier'],  'ghi'] = nan

                del df_clean['dni_outlier']
                del df_clean['dhi_outlier']
                del df_clean['ghi_outlier']
                rv_outliers.set(df_clean)
            else:
                rv_outliers.set(df_clean)
                



    # load into DuckDB
    @output
    @render.ui
    @reactive.event(input.btn_load)
    async def load_status():
        df = rv_outliers.get().copy()
        
        df = df.reset_index()
        print(df.info())
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

        long_df = df.melt(
            id_vars=['timestamp'],
            var_name='variable',
            value_name='value'
        )
        long_df.columns = ['date', 'variable', 'value']
        df_load = long_df


        with ui.Progress(min=1, max=len(df_load)) as p:
            p.set(message="Iniciando carga…")
            con = duckdb.connect(db_name)
            con.execute("""
                CREATE TABLE IF NOT EXISTS lecturas (
                    date TIMESTAMP,
                    variable VARCHAR,
                    value DOUBLE,
                    PRIMARY KEY (date, variable)
                );
            """)
            con.execute("BEGIN TRANSACTION;")
            chunk = 5000
            for i in range(0, len(df_load), chunk):
                c = df_load.iloc[i : i + chunk]
                con.register('tmp', c)
                con.execute("INSERT INTO lecturas SELECT * FROM tmp ON CONFLICT DO NOTHING;")
                p.set(i + chunk, message=f"Cargando filas {i+1}-{min(i+chunk, len(df_load))}…")
            con.execute("COMMIT;")
            con.close()
        return ui.tags.div("Carga completada", class_="text-success")

    @output  # id="export_database" implícito
    @render.download(filename="ClimaLab.parquet",
                    media_type="application/x-parquet")  # opcional pero útil
    def export_database():
        # 1) Read and pivot df
        con = duckdb.connect(db_name)
        df = (
            con.execute("SELECT * FROM lecturas ORDER BY date")
            .fetchdf()
            .pivot(index="date", columns="variable", values="value")
        )
        con.close()

        # 2) Write parquet to buffer in memory
        with io.BytesIO() as buf:
            df.to_parquet(buf, index=True, engine="pyarrow")
            buf.seek(0)
            yield buf.getvalue()       # <-- clave: yield bytes

            
    @output
    @render.ui
    @reactive.event(input.btn_delete)
    async def delete_status():
        db_path = db_name
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                return ui.tags.div("Base de datos eliminada", class_="text-danger")
            except PermissionError:
                return ui.tags.div(
                    "No se puede eliminar: cierre las conexiones abiertas o reinicie la app.",
                    class_="text-danger"
                )
            except Exception as e:
                return ui.tags.div(f"Error al eliminar la base de datos: {e}", class_="text-danger")
        else:
            return ui.tags.div("No se encontró la base de datos.", class_="text-warning")

    # render outputs
    # @render_plotly
    # def plot_plotly():
    
    @output
    @render.plot
    def missingno_plot():
        df = rv_loaded.get()   # DataFrame cargado reactivo
        if df is None:
            return None
        return plot_missingno(df)

    @render_plotly
    def plot_radiacion():
        return rv_rad_plot.get()


    @render.data_frame
    def df_types():
        return rv_types.get()

    @render.data_frame
    def df_radiacion():
        return rv_clean.get()


    @render.ui
    def table_tests():
        tests = rv_tests.get() or {}
        rows = []
        for test, ok in tests.items():
            icon = "circle-check" if ok else "circle-exclamation"
            color = "text-success" if ok else "text-danger"
            rows.append(
                ui.tags.tr(
                    ui.tags.td(test, style="text-align:left;"),
                    ui.tags.td(fa.icon_svg(icon).add_class(color), style="text-align:center;"),
                )
            )
        return ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("Test", style="text-align:left;"),
                    ui.tags.th("State", style="text-align:center;"),
                )
            ),
            ui.tags.tbody(*rows),
            class_="table table-sm table-striped w-auto",
        )

# instantiate app
app = App(app_ui, server,debug=False)
