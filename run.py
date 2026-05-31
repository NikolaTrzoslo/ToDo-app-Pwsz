from pathlib import Path
import json

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QListWidgetItem, QLineEdit, QPushButton, QCheckBox
from PySide6.QtUiTools import QUiLoader


BASE_DIR = Path(__file__).resolve().parent
TASKS_FILE = BASE_DIR / "tasks.json"


def load_ui(loader: QUiLoader, filename: str):
	ui_file = QFile(str(BASE_DIR / filename))
	if not ui_file.open(QFile.ReadOnly):
		raise RuntimeError(f"Nie można otworzyć pliku UI: {filename}")
	try:
		return loader.load(ui_file)
	finally:
		ui_file.close()


def get_widget(parent, widget_type, object_name: str):
	widget = parent.findChild(widget_type, object_name)
	if widget is None:
		raise RuntimeError(f"Brak widgetu {object_name} w załadowanym UI")
	return widget


def resource_path(filename: str) -> Path:
	return BASE_DIR / filename


def apply_window_icons(main_window):
	add_button = get_widget(main_window, QPushButton, "Dodaj")
	add_button.setIcon(QIcon(str(resource_path("add-new-3.png"))))

	logo_label = get_widget(main_window, type(main_window.label_2), "label_2")
	logo_label.setPixmap(QPixmap(str(resource_path("04-sfa_-temporary-tasks.png"))))


def apply_task_state(line_edit: QLineEdit, checked: bool):
	font = line_edit.font()
	font.setStrikeOut(checked)
	line_edit.setFont(font)
	text_color = "#A0A0A0" if checked else "#444"
	line_edit.setStyleSheet(
		f"QLineEdit {{"
		f" background: #FFFFFF;"
		f" border: 1px solid #E8C7CC;"
		f" border-radius: 8px;"
		f" padding: 6px 10px;"
		f" color: {text_color};"
		f" font-size: 12pt;"
		f"}}"
	)


def serialize_tasks(list_widget):
	tasks = []
	for index in range(list_widget.count()):
		item = list_widget.item(index)
		row_widget = list_widget.itemWidget(item)
		if row_widget is None:
			continue
		line_edit = row_widget.findChild(QLineEdit, "lineEdit2")
		check_box = row_widget.findChild(QCheckBox, "checkBox")
		if line_edit is None or check_box is None:
			continue
		tasks.append({"text": line_edit.text(), "completed": check_box.isChecked()})
	return tasks


def save_tasks(list_widget):
	data = serialize_tasks(list_widget)
	TASKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_vertical_scrollbars(list_widget, external_scrollbar):
	list_widget.doItemsLayout()
	list_widget.updateGeometries()
	internal_scrollbar = list_widget.verticalScrollBar()
	external_scrollbar.blockSignals(True)
	external_scrollbar.setRange(internal_scrollbar.minimum(), internal_scrollbar.maximum())
	external_scrollbar.setPageStep(internal_scrollbar.pageStep())
	external_scrollbar.setSingleStep(internal_scrollbar.singleStep())
	external_scrollbar.setValue(internal_scrollbar.value())
	external_scrollbar.blockSignals(False)


def update_vertical_scrollbar(main_window):
	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	external_scrollbar = get_widget(main_window, type(main_window.verticalScrollBar), "verticalScrollBar")
	sync_vertical_scrollbars(list_widget, external_scrollbar)


def load_saved_tasks(main_window, loader: QUiLoader):
	if not TASKS_FILE.exists():
		return

	try:
		tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return

	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	for task in tasks:
		if not isinstance(task, dict):
			continue
		text = str(task.get("text", "")).strip()
		if not text:
			continue
		add_task_to_list(main_window, loader, text=text, checked=bool(task.get("completed", False)), save=False)


def remove_task_from_list(main_window, item):
	row = main_window.listWidget.row(item)
	if row < 0:
		return

	widget = main_window.listWidget.itemWidget(item)
	if widget is not None:
		widget.deleteLater()

	main_window.listWidget.takeItem(row)
	save_tasks(main_window.listWidget)
	update_vertical_scrollbar(main_window)


def add_task_to_list(main_window, loader: QUiLoader, text: str | None = None, checked: bool = False, save: bool = True):
	line_edit1 = get_widget(main_window, QLineEdit, "lineEdit1")
	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	task_text = line_edit1.text().strip() if text is None else text.strip()
	if not task_text:
		return

	row_widget = load_ui(loader, "Form.ui")
	line_edit = get_widget(row_widget, QLineEdit, "lineEdit2")
	delete_button = get_widget(row_widget, QPushButton, "usun")
	edit_button = get_widget(row_widget, QPushButton, "Edit")
	check_box = get_widget(row_widget, QCheckBox, "checkBox")
	delete_button.setIcon(QIcon(str(resource_path("delete-851.png"))))
	edit_button.setIcon(QIcon(str(resource_path("edit-644.png"))))

	line_edit.setText(task_text)
	line_edit.setReadOnly(True)
	check_box.setChecked(checked)
	apply_task_state(line_edit, checked)
	row_widget.adjustSize()
	row_widget.setMinimumHeight(max(row_widget.minimumHeight(), row_widget.sizeHint().height()))
	row_widget.setFixedWidth(list_widget.viewport().width())

	item = QListWidgetItem()
	item.setSizeHint(row_widget.size())
	list_widget.addItem(item)
	list_widget.setItemWidget(item, row_widget)

	check_box.toggled.connect(lambda is_checked: apply_task_state(line_edit, is_checked))
	check_box.toggled.connect(lambda _: save_tasks(list_widget))
	delete_button.clicked.connect(lambda: remove_task_from_list(main_window, item))
	edit_button.clicked.connect(lambda: (line_edit.setReadOnly(False), line_edit.setFocus()))
	line_edit.editingFinished.connect(lambda: line_edit.setReadOnly(True))
	line_edit.textChanged.connect(lambda _: save_tasks(list_widget))

	if text is None:
		line_edit1.clear()
		line_edit1.setFocus()

	if save:
		save_tasks(list_widget)
		update_vertical_scrollbar(main_window)


def main():
	app = QApplication([])
	loader = QUiLoader()
	window = load_ui(loader, "Main.ui")
	list_widget = get_widget(window, type(window.listWidget), "listWidget")
	external_scrollbar = get_widget(window, type(window.verticalScrollBar), "verticalScrollBar")
	apply_window_icons(window)
	list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
	list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
	list_widget.verticalScrollBar().rangeChanged.connect(lambda *_: sync_vertical_scrollbars(list_widget, external_scrollbar))
	list_widget.verticalScrollBar().valueChanged.connect(external_scrollbar.setValue)
	external_scrollbar.valueChanged.connect(list_widget.verticalScrollBar().setValue)
	add_button = get_widget(window, QPushButton, "Dodaj")
	add_button.clicked.connect(lambda: add_task_to_list(window, loader))
	load_saved_tasks(window, loader)
	app.aboutToQuit.connect(lambda: save_tasks(list_widget))
	window.show()
	app.processEvents()
	update_vertical_scrollbar(window)
	app.exec()


if __name__ == "__main__":
	main()