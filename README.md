# Dokumentacja

## Uruchomienie programu w trybie –init:
``` python3 API.py <plik.json> --init ```

## Uruchomienie programu:
``` python3 API.py <plik.json> ```

### Program czyta plik .json linia po linii i w zależności od podanej operacji wywołuje odpowiednią funkcję:
* **open** – ```openf()```: <br> w przypadku ```–init``` następuje inicjalizacja tablic, pgcrypto oraz utworzenie użytkownika *app* z prawami SELECT, INSERT, UPDATE, DELETE. Zawsze następuje próba połączenia z bazą.
* **root** – ```root()```: <br> jeśli pole secret ma poprawną zawartość(*qwerty*), to dodaje roota do tabeli *people* i *parents*. Funkcja ```check()``` sprawdza, czy wpis już istnieje.
* **new** – ```new()```: <br> w przypadkach zgodnych z specyfikacją korzysta z funkcji ```adder()```, by dodać osobę do wszystkich trzech tabel. Do tabeli *children* dodaje id rodzica. Funkcja ```check()``` sprawdza, czy wpis już istnieje.
* **remove** – ```remove()```: <br> tworzy listę wszystkich potomków wraz z samym sobą. Dla każdego z nich usuwa odpowiednie rzędy w trzech tabelach.
* **child** – ```child()```: <br> korzystając z tabeli *children*, zwraca wszystkie dzieci danej osoby.
* **parent** – ```parents()```: <br> korzystając z tabeli *parents*, zwraca rodzica danej osoby.
* **ancestors** – ```ancestors()```: <br> w pętli dodaje rodziców do listy, aż do momentu kiedy dojdzie do roota.
* **descendants** – ```descendants()```: <br> działa analogicznie do ```ancestors()```, tyle że z użyciem ```child()``` oraz dodatkowej funkcji ```descendants_helper()```. W pętli dodaje dzieci do listy, aż do momentu zejścia do liścia.
* **ancestor** – ```ancestor()```: <br> sprawdza czy odpowiednie id znajduje się w liście przodków – w tym celu korzysta z funkcji ```ancestors()```
* **read** – ```read()```: <br> korzystając z ```read_data()``` oraz tabeli *people*, zwraca zawartość pola ```<data>```.
* **update** – ```update()```: <br> używając ```update_data()``` zmienia zawartość pola ```<data>```.

Hasła są hashowane, walidacja następuje w jednym, bądź dwóch krokach, w zależności od polecenia. Sprawdzenie poprawności hasła następuje zaraz przed rozważeniem przypadków operacji, które potrzebują owej walidacji. Jeśli polecenie dodatkowo wymaga, by ```<admin>``` był odpowiednio wysoko w hierarchii, następuje to wewnątrz funkcji obsługującej daną operację.