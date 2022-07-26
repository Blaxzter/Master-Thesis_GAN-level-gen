import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from test.TestEnvironment import TestEnvironment
from test.visualization.LevelVisualisation import create_plotly_data

current_figure = None

if __name__ == '__main__':
    test_environment = TestEnvironment('generated/single_structure')

    level_img_encoder = LevelImgEncoder()

    app = dash.Dash(__name__)

    app.layout = html.Div([
        dcc.Markdown("# Level Visualisation"),
        html.Div([
            html.Div([
                dcc.Markdown("## Encoding"),
                dcc.Checklist(
                    id = "encoding",
                    options = [
                        {"label": 'Multilayer', "value": 'multi_layer'},
                        {"label": 'Only One', "value": 'only_one'},
                        {"label": 'Zero Included', "value": 'zero_included'},
                    ],
                    value = ['multi_layer']
                )
            ], style = {'margin-right': '3em'}),
            html.Div([
                dcc.Markdown("## Level Selection"),
                dcc.Input(
                    id = "level_selection",
                    type = "number",
                    value = 0,
                    placeholder = "input type {}".format("number"),
                )]
            )], style = {'display': 'flex'}),
        dcc.Graph(id = "voxel-chart", style = {'height': '90vh'}),
    ])


    @app.callback(
        Output("voxel-chart", "figure"),
        [
            Input("encoding", "value"),
            Input("level_selection", "value")
        ]
    )
    def update_line_chart(encoding, level_selection):

        level = test_environment.get_level(level_selection)
        if 'only_one' in encoding:
            level_img = level_img_encoder.create_one_element_img(
                level.get_used_elements(),
                'multi_layer' in encoding
            )
        else:
            level_img = level_img_encoder.create_calculated_img(level.get_used_elements())

            if 'multi_layer' in encoding:
                level_img = level_img_encoder.create_multi_dim_img_from_picture(
                    level_img, zero_included = 'zero_included' in encoding)

        level_img = np.flip(level_img, axis = 0)

        plotly_data = create_plotly_data(level_img)
        fig = go.Figure(data = plotly_data)
        fig.update_layout(scene = dict(
            aspectmode = 'data',
            camera = dict(
                up = dict(x = 0, y = 0, z = 1),
                eye = dict(x = 0., y = 0., z = 2.5),
                center = dict(x = 0, y = 0, z = 0),
            )
        ))

        fig.layout.uirevision = True
        global current_figure

        current_figure = fig
        return fig


    app.run_server(debug = True, port = 5052)
