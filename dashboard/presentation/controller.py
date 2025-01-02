from typing import Optional
import dash
import dash_bootstrap_components as dbc

from services.data_service import DataService
from presentation.layout_builder import LayoutBuilder
from presentation.callback_register import CallbackRegister


class DashAppController:
    """
    Clase principal que orquesta la aplicación Dash.
    - Inicializa la app Dash.
    - Inyecta el data_service.
    - Crea el layout a través de LayoutBuilder.
    - Registra los callbacks a través de CallbackRegistrar.
    - Expone un método run() para lanzar el servidor.
    """

    def __init__(self, 
                 data_service: DataService, 
                 layout_builder: LayoutBuilder, 
                 callback_registrar: CallbackRegister) -> None:
        """
        :param data_service: Instancia de DataService para la capa de negocio.
        :param layout_builder: Objeto encargado de construir el layout.
        :param callback_registrar: Objeto encargado de registrar los callbacks.
        """
        self.data_service: DataService = data_service
        
        # Inicializamos la app de Dash
        self.app: dash.Dash = dash.Dash(
            __name__,
            external_stylesheets = [dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions = True
        )

        # Construimos el layout principal
        self.app.layout = layout_builder.create_layout()

        # Registramos los callbacks necesarios
        callback_registrar.register_callbacks(self.app)

    def run(self, debug: bool = True, port: Optional[int] = 8050) -> None:
        """
        Inicia el servidor de Dash.
        """
        self.app.run_server(debug = debug, port = port)