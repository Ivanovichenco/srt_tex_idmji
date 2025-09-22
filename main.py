import flet as ft
from flet import MainAxisAlignment, CrossAxisAlignment, PagePlatform
import threading
import subprocess
import os

# Import the downloader logic
from downloader import download_subtitles, is_playlist

# Global variable to store the download folder path
download_folder_path = None

def main(page: ft.Page):
    page.title = "Descargador de Subtítulos de YouTube"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 700
    page.window_height = 500
    page.window_resizable = False

    # --- UI Controls ---
    url_input = ft.TextField(
        label="URL del video o playlist de YouTube",
        width=450,
        border_radius=10,
        border_color=ft.Colors.WHITE24,
    )

    download_button = ft.ElevatedButton(
        text="Descargar",
        icon=ft.Icons.DOWNLOAD,
        width=200,
        height=55,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )
    )

    # --- Playlist choice buttons (initially hidden) ---
    download_video_button = ft.ElevatedButton(
        text="Solo Video",
        icon=ft.Icons.VIDEO_FILE,
        width=200,
        height=55,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_GREY_700,
            color=ft.Colors.WHITE,
        ),
    )
    download_playlist_button = ft.ElevatedButton(
        text="Lista Completa",
        icon=ft.Icons.PLAYLIST_ADD_CHECK,
        width=200,
        height=55,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        ),
    )
    choice_row = ft.Row(
        [download_video_button, download_playlist_button],
        alignment=MainAxisAlignment.CENTER,
        spacing=20,
        visible=False
    )

    new_download_button = ft.ElevatedButton(
        text="Nueva Descarga",
        icon=ft.Icons.REFRESH,
        width=200,
        height=55,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.GREY_700,
            color=ft.Colors.WHITE,
        )
    )

    open_folder_button = ft.ElevatedButton(
        text="Abrir Carpeta",
        icon=ft.Icons.FOLDER_OPEN,
        width=200,
        height=55,
        disabled=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
        )
    )

    status_text = ft.Text(value="", text_align=ft.TextAlign.CENTER, size=16)
    progress_ring = ft.ProgressRing(visible=False, width=24, height=24)

    status_row = ft.Row(
        [
            progress_ring,
            status_text,
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False,
    )

    # --- Functions ---
    def reset_ui(e):
        url_input.value = ""
        url_input.visible = True
        status_text.value = ""
        status_row.visible = False
        download_button.visible = True
        download_button.disabled = False
        choice_row.visible = False
        open_folder_button.disabled = True
        page.update()

    def open_download_folder(e):
        if download_folder_path:
            try:
                if page.platform == ft.PagePlatform.LINUX:
                    subprocess.run(["xdg-open", download_folder_path])
                elif page.platform == ft.PagePlatform.WINDOWS:
                    os.startfile(download_folder_path)
                elif page.platform == ft.PagePlatform.MACOS:
                    subprocess.run(["open", download_folder_path])
                else:
                    status_text.value = "Plataforma no soportada para abrir carpeta."
            except Exception as ex:
                status_text.value = f"Error al abrir carpeta: {ex}"
        page.update()

    new_download_button.on_click = reset_ui
    open_folder_button.on_click = open_download_folder

    # --- Download Logic ---
    def start_download_thread(download_playlist: bool):
        global download_folder_path
        video_url = url_input.value

        # Set UI to downloading state
        choice_row.visible = False
        status_row.visible = True
        progress_ring.visible = True
        status_text.value = "Iniciando descarga..."
        status_text.color = ft.Colors.WHITE70
        page.update()

        def download_worker():
            global download_folder_path
            success, result = download_subtitles(video_url, download_playlist)
            
            def update_ui():
                global download_folder_path
                progress_ring.visible = False
                if success:
                    download_folder_path = result
                    status_text.value = f"Descarga completada en: '{result}'"
                    status_text.color = ft.Colors.GREEN_400
                    open_folder_button.disabled = False
                else:
                    status_text.value = result
                    status_text.color = ft.Colors.RED_400
                    open_folder_button.disabled = True
                page.update()
            
            page.run_thread(update_ui)

        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()

    def handle_download_choice(e):
        download_playlist = (e.control == download_playlist_button)
        start_download_thread(download_playlist)

    download_video_button.on_click = handle_download_choice
    download_playlist_button.on_click = handle_download_choice

    def check_url_and_download(e):
        video_url = url_input.value
        if not video_url:
            status_row.visible = True
            status_text.value = "Por favor, introduce una URL."
            status_text.color = ft.Colors.AMBER_500
            page.update()
            return

        if is_playlist(video_url):
            # Show choice buttons
            download_button.visible = False
            choice_row.visible = True
            status_row.visible = True
            status_text.value = "Este video pertenece a una lista. ¿Qué quieres descargar?"
            status_text.color = ft.Colors.WHITE
            page.update()
        else:
            # Download single video directly
            download_button.disabled = True
            start_download_thread(download_playlist=False)

    download_button.on_click = check_url_and_download

    # --- Layout ---
    main_column = ft.Column(
        [
            ft.Text("Descargador SRT / TXT", size=32, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Pega la URL de un video o playlist de YouTube para obtener los subtítulos.",
                size=16,
                color=ft.Colors.WHITE70,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(height=30, color="transparent"),
            url_input,
            ft.Divider(height=15, color="transparent"),
            download_button, # Main download button
            choice_row, # Initially hidden choice buttons
            ft.Divider(height=15, color="transparent"),
            ft.Row(
                [new_download_button, open_folder_button],
                alignment=MainAxisAlignment.CENTER,
                spacing=20,
            ),
            ft.Divider(height=20, color="transparent"),
            status_row,
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=10,
    )

    page.add(
        ft.Container(
            content=main_column,
            width=620,
            padding=40,
            border_radius=15,
            bgcolor="rgba(255, 255, 255, 0.03)",
            border=ft.border.all(1, ft.Colors.WHITE10),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color="rgba(0, 0, 0, 0.1)",
                offset=ft.Offset(0, 0),
            )
        )
    )

if __name__ == "__main__":
    # Flet entry point
    def page_run_thread(target, *args, **kwargs):
        threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True).start()

    ft.app(target=main)
    ft.Page.run_thread = page_run_thread
