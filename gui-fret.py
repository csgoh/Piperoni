import flet as ft
from flet import Theme, Icon
import logging
import os
from PIL import Image
from processpiper.text2diagram import render

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("flet_core").setLevel(logging.ERROR)


def main(page: ft.page):
    selected_file: str
    generated_image: Image
    test_str: str = "test"

    def close_app(e):
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    test_text = """
    title: Make pizza process
    lane: Pizza Shop
        (start) as start
        [Put the pizza in the oven] as put_pizza_in_oven
        [Check to see if pizza is done] as check_pizza_done
        <Done baking?> as done_baking
        [Take the pizza out of the oven] as take_pizza_out_of_oven
        (end) as end

    start->put_pizza_in_oven->check_pizza_done->done_baking
    done_baking-"Yes"->take_pizza_out_of_oven->end
    done_baking-"No"->put_pizza_in_oven
    """
    # page.theme = Theme(font_family="Arial", color_scheme_seed="green")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.update()

    # page.window_title_bar_hidden = True

    page.title = "Process Piper"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.window_height = 800
    page.window_width = 1200
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.PALETTE),
        leading_width=40,
        title=ft.Text("Text to BPMN Diagram"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.icons.WB_SUNNY_OUTLINED),
            ft.IconButton(ft.icons.FILTER_3),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="Item 1"),
                    ft.PopupMenuItem(),  # divider
                    ft.PopupMenuItem(text="Checked item", checked=False),
                ]
            ),
            ft.IconButton(ft.icons.EXIT_TO_APP, on_click=close_app),
        ],
    )

    def yes_click(e):
        page.window_destroy()

    def no_click(e):
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you really want to exit this app?"),
        actions=[
            ft.ElevatedButton("Yes", on_click=yes_click),
            ft.OutlinedButton("No", on_click=no_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def generate_diagram(e):
        diagram_text = user_input.value

        try:
            nonlocal generated_image
            generated_code, generated_image = render(diagram_text)
            save_diagram_button.visible = True
            output_image_file = "diagram.png"
            if os.path.exists(output_image_file):
                # delete output_image_file
                os.remove(output_image_file)

            generated_image.save(output_image_file)

            output_image.src = output_image_file
            output_image.update()
            page.update()

        except Exception as e:
            log_text.value = log_text.value + "\n" + str(e)
            page.update()
            generated_image = None

    def pick_files_result(e: ft.FilePickerResultEvent):
        selected_file = e.path if e.path else "Cancelled!"
        if ".png" not in selected_file:
            selected_file = selected_file + ".png"

        if selected_file != "Cancelled!":
            if ".png" not in selected_file:
                selected_file = selected_file + ".png"
            nonlocal generated_image
            generated_image.save(selected_file, "PNG")
            print(f"Image saved at {selected_file}")
        print(f">>>Save Path {selected_file}")

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    def show_picker(e):
        try:
            pick_files_dialog.save_file(allowed_extensions=["png"])
            print(f"<<<<< save_file() return")

        except Exception as e:
            log_text.value = log_text.value + "\n" + str(e)
            page.update()

    user_input = ft.TextField(
        label="Enter text here",
        value=test_text,
        multiline=True,
        text_size=11,
        # color="black",
        # bgcolor="white",
        icon=ft.icons.TEXT_FIELDS_SHARP,
    )
    generate_button = ft.ElevatedButton(
        "Generate", on_click=generate_diagram, icon=ft.icons.DIRECTIONS_RUN
    )
    output_image = ft.Image("Output Image", fit=ft.ImageFit.CONTAIN)
    save_diagram_button = ft.ElevatedButton(
        "Save Diagram", on_click=show_picker, visible=False
    )

    log_text = ft.TextField(
        label="Log Messages",
        value="",
        multiline=True,
        read_only=True,
        text_size=11,
        color="black",
        bgcolor="white",
    )

    page.add(
        user_input,
        generate_button,
        output_image,
        save_diagram_button,
        log_text,
    )


ft.app(target=main)
