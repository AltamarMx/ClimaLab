from shiny import reactive, render, ui
from utils.thermal_comfort import (
    plot_utci, 
    plot_heatmap_zona_confort_Morillon, 
    plot_confort_adaptativo,
    graficar_DDH_por_periodos,
)



def thermal_comfort_server(input, output, session):
    @output
    @render.ui
    def plotly_plot():
        seleccion = input.lineas()
        columnas = []
        for item in seleccion:
            if item == "ASHRAE_80":
                columnas.extend(["tmp_cmf_80_low", "tmp_cmf_80_up"])
            elif item == "ASHRAE_90":
                columnas.extend(["tmp_cmf_90_low", "tmp_cmf_90_up"])
            elif item == "Morillon":
                columnas.extend(["Lim_inf_Morillon", "Lim_sup_Morillon"])
            else:
                columnas.append(item)

        fig = plot_confort_adaptativo(columnas)
        return ui.HTML(fig.to_html(full_html=False))

    @output
    @render.ui
    def ddh_plot():
        r1 = (input.rango_1_ddh()[0].strftime('%Y-%m-%d'), input.rango_1_ddh()[1].strftime('%Y-%m-%d'))
        r2 = (input.rango_2_ddh()[0].strftime('%Y-%m-%d'), input.rango_2_ddh()[1].strftime('%Y-%m-%d'))

        fig = graficar_DDH_por_periodos([r1, r2], modelo=input.modelo_ddh())
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))

    @output
    @render.plot
    def heatmap_plot():
        year_range = input.years_heatmap()
        years = list(range(year_range[0], year_range[1] + 1))
        return plot_heatmap_zona_confort_Morillon(years)

    @output
    @render.plot
    def utci_plot():
        r1 = (input.rango_1_utci()[0].strftime('%Y-%m-%d'), input.rango_1_utci()[1].strftime('%Y-%m-%d'))
        r2 = (input.rango_2_utci()[0].strftime('%Y-%m-%d'), input.rango_2_utci()[1].strftime('%Y-%m-%d'))
        return plot_utci(rangos=[r1, r2]) 