# ToDo-app — uruchomienie lokalne

Kroki, aby uruchomić aplikację lokalnie (Windows, cmd):

1. Utwórz virtual environment w folderze projektu:

```powershell
python -m venv .venv
```

2. Aktywuj środowisko:

```powershell
.venv\Scripts\activate
```

3. Zaktualizuj pip i zainstaluj zależności:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Zbuduj plik `.exe` z ikonami i uruchom aplikację:

```powershell
pyinstaller run.spec
```

Po zbudowaniu gotowy plik znajdziesz w `dist\run.exe`.

Uwaga: jeśli widzisz komunikat "externally-managed-environment" (MSYS2), nadal możesz utworzyć virtualenv jak wyżej — użycie `python -m venv .venv` utworzy izolowane środowisko z działającym `pip`.
