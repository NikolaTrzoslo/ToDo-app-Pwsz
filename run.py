
# import biblioteki do pracy ze sciezkami i json-em
from pathlib import Path
import json

# importy z biblioteki pyside6 potrzebne do interfejsu
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QListWidgetItem, QLineEdit, QPushButton, QCheckBox
from PySide6.QtUiTools import QUiLoader


# ustawiamy katalog bazowy (tam gdzie jest ten plik)
BASE_DIR = Path(__file__).resolve().parent
# plik z zadaniami, do ktorego zapisujemy/odczytujemy
TASKS_FILE = BASE_DIR / "tasks.json"


def load_ui(loader: QUiLoader, filename: str):
	# funkcja wczytuje plik .ui i zwraca załadowane okno/widget
	ui_file = QFile(str(BASE_DIR / filename))
	# probujemy otworzyc plik ui tylko do odczytu
	if not ui_file.open(QFile.ReadOnly):
		# jak nie mozna otworzyc to rzucamy blad
		raise RuntimeError(f"Nie można otworzyć pliku UI: {filename}")
	try:
		# loader wczyta widget z pliku
		return loader.load(ui_file)
	finally:
		# zawsze zamykamy plik
		ui_file.close()


def get_widget(parent, widget_type, object_name: str):
	# znajdz dziecko (widget) po nazwie i typie
	widget = parent.findChild(widget_type, object_name)
	if widget is None:
		# jesli nie ma widgetu to blad
		raise RuntimeError(f"Brak widgetu {object_name} w załadowanym UI")
	return widget


def resource_path(filename: str) -> Path:
	# zwraca sciezke do pliku zasobu w katalogu projektu
	return BASE_DIR / filename


def apply_window_icons(main_window):
	# przypisuje ikony do przyciskow/etykiet w glownej ramce
	add_button = get_widget(main_window, QPushButton, "Dodaj")
	add_button.setIcon(QIcon(str(resource_path("add-new-3.png"))))

	# ustawiam logo/obrazek w labelce
	logo_label = get_widget(main_window, type(main_window.label_2), "label_2")
	logo_label.setPixmap(QPixmap(str(resource_path("04-sfa_-temporary-tasks.png"))))


def apply_task_state(line_edit: QLineEdit, checked: bool):
	# zmienia wyglad pola tekstowego zależnie od stanu checkboxa
	font = line_edit.font()
	# przekreslamy tekst jak zadanie wykonane
	font.setStrikeOut(checked)
	line_edit.setFont(font)
	# wybieramy kolor tekstu dla wykonanych/nie wykonanych
	text_color = "#A0A0A0" if checked else "#444"
	# ustawiamy style css dla pola tekstowego
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
	# bierze wszystkie wiersze z listy i zamienia na liste slownikow
	tasks = []
	for index in range(list_widget.count()):
		# pobieramy element listy po indeksie
		item = list_widget.item(index)
		# pobieramy widget przypisany do tego elementu (wiersz)
		row_widget = list_widget.itemWidget(item)
		if row_widget is None:
			# jak nie ma widgetu to przejdz dalej
			continue
		# w wierszu szukamy pola tekstowego i checkboxa
		line_edit = row_widget.findChild(QLineEdit, "lineEdit2")
		check_box = row_widget.findChild(QCheckBox, "checkBox")
		if line_edit is None or check_box is None:
			continue
		# dodajemy do listy slownik z tekstem i statusem
		tasks.append({"text": line_edit.text(), "completed": check_box.isChecked()})
	return tasks


def save_tasks(list_widget):
	# serializujemy i zapisujemy do pliku json
	data = serialize_tasks(list_widget)
	TASKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_vertical_scrollbars(list_widget, external_scrollbar):
	# synchronizuje pasek przewijania listy z zewnetrznym paskiem
	list_widget.doItemsLayout()
	list_widget.updateGeometries()
	internal_scrollbar = list_widget.verticalScrollBar()
	# blokujemy sygnaly zeby nie tworzyc petli
	external_scrollbar.blockSignals(True)
	# ustawiamy zakres i kroki z wewnetrznego paska
	external_scrollbar.setRange(internal_scrollbar.minimum(), internal_scrollbar.maximum())
	external_scrollbar.setPageStep(internal_scrollbar.pageStep())
	external_scrollbar.setSingleStep(internal_scrollbar.singleStep())
	external_scrollbar.setValue(internal_scrollbar.value())
	external_scrollbar.blockSignals(False)


def update_vertical_scrollbar(main_window):
	# znajduje widget listy i zewnetrzny pasek, potem synchronizuje
	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	external_scrollbar = get_widget(main_window, type(main_window.verticalScrollBar), "verticalScrollBar")
	sync_vertical_scrollbars(list_widget, external_scrollbar)


def load_saved_tasks(main_window, loader: QUiLoader):
	# jesli plik z zadaniami nie istnieje to nic nie robimy
	if not TASKS_FILE.exists():
		return

	try:
		# czytamy plik json i parsujemy
		tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		# jak blad przy odczycie/parsing to wychodzimy
		return

	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	for task in tasks:
		# sprawdzamy czy zadanie ma poprawny format
		if not isinstance(task, dict):
			continue
		text = str(task.get("text", "")).strip()
		if not text:
			continue
		# dodajemy kazde zadanie do listy ale bez zapisu do pliku
		add_task_to_list(main_window, loader, text=text, checked=bool(task.get("completed", False)), save=False)


def remove_task_from_list(main_window, item):
	# usuwa element z listy i aktualizuje plik
	row = main_window.listWidget.row(item)
	if row < 0:
		return

	widget = main_window.listWidget.itemWidget(item)
	if widget is not None:
		# zwalniamy widget
		widget.deleteLater()

	# usuwamy element z listy
	main_window.listWidget.takeItem(row)
	# zapisujemy zmiany i aktualizujemy pasek
	save_tasks(main_window.listWidget)
	update_vertical_scrollbar(main_window)


def add_task_to_list(main_window, loader: QUiLoader, text: str | None = None, checked: bool = False, save: bool = True):
	# dodaje nowy wiersz z zadaniem do listy
	line_edit1 = get_widget(main_window, QLineEdit, "lineEdit1")
	list_widget = get_widget(main_window, type(main_window.listWidget), "listWidget")
	# jesli nie podano tekstu, bierzemy z pola wejsciowego
	task_text = line_edit1.text().strip() if text is None else text.strip()
	if not task_text:
		# nie dodajemy pustych zadan
		return

	# ladujemy szablon wiersza z pliku ui
	row_widget = load_ui(loader, "Form.ui")
	line_edit = get_widget(row_widget, QLineEdit, "lineEdit2")
	delete_button = get_widget(row_widget, QPushButton, "usun")
	edit_button = get_widget(row_widget, QPushButton, "Edit")
	check_box = get_widget(row_widget, QCheckBox, "checkBox")
	# ustawiamy ikony dla przyciskow
	delete_button.setIcon(QIcon(str(resource_path("delete-851.png"))))
	edit_button.setIcon(QIcon(str(resource_path("edit-644.png"))))

	# ustawiamy tekst w polu wiersza i parametry
	line_edit.setText(task_text)
	line_edit.setReadOnly(True)
	check_box.setChecked(checked)
	apply_task_state(line_edit, checked)
	row_widget.adjustSize()
	row_widget.setMinimumHeight(max(row_widget.minimumHeight(), row_widget.sizeHint().height()))
	row_widget.setFixedWidth(list_widget.viewport().width())

	# tworzymy element listy i przypisujemy widget
	item = QListWidgetItem()
	item.setSizeHint(row_widget.size())
	list_widget.addItem(item)
	list_widget.setItemWidget(item, row_widget)

	# podpinamy sygnaly: checkbox, usun, edytuj, zmiana tekstu
	check_box.toggled.connect(lambda is_checked: apply_task_state(line_edit, is_checked))
	check_box.toggled.connect(lambda _: save_tasks(list_widget))
	delete_button.clicked.connect(lambda: remove_task_from_list(main_window, item))
	edit_button.clicked.connect(lambda: (line_edit.setReadOnly(False), line_edit.setFocus()))
	line_edit.editingFinished.connect(lambda: line_edit.setReadOnly(True))
	line_edit.textChanged.connect(lambda _: save_tasks(list_widget))

	# jesli dodajemy z pola wejsciowego to wyczysc pole i ustaw fokus
	if text is None:
		line_edit1.clear()
		line_edit1.setFocus()

	if save:
		# zapis i synchronizacja paska
		save_tasks(list_widget)
		update_vertical_scrollbar(main_window)


def main():
	# funkcja glowna uruchamiajaca aplikacje
	app = QApplication([])
	loader = QUiLoader()
	window = load_ui(loader, "Main.ui")
	list_widget = get_widget(window, type(window.listWidget), "listWidget")
	external_scrollbar = get_widget(window, type(window.verticalScrollBar), "verticalScrollBar")
	apply_window_icons(window)
	# wylaczamy poziome przewijanie i zarzadzamy pionowym recznie
	list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
	list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
	list_widget.verticalScrollBar().rangeChanged.connect(lambda *_: sync_vertical_scrollbars(list_widget, external_scrollbar))
	list_widget.verticalScrollBar().valueChanged.connect(external_scrollbar.setValue)
	external_scrollbar.valueChanged.connect(list_widget.verticalScrollBar().setValue)
	add_button = get_widget(window, QPushButton, "Dodaj")
	add_button.clicked.connect(lambda: add_task_to_list(window, loader))
	# ladujemy zapisane zadania z pliku
	load_saved_tasks(window, loader)
	# przy zamykaniu aplikacji zapisujemy zadania
	app.aboutToQuit.connect(lambda: save_tasks(list_widget))
	window.show()
	app.processEvents()
	update_vertical_scrollbar(window)
	app.exec()


if __name__ == "__main__":
	main()