#!/usr/bin/env python3
"""
Analyze dimension columns in EDI CSV
"""
import pandas as pd

df = pd.read_csv('assets/EDI Export Artikeldaten.csv', sep=';', encoding='utf-8')

print('='*80)
print('VERGLEICH: Bezeichnung vs. verschiedene Maß-Spalten (erste 5):')
print('='*80)

for i in range(5):
    row = df.iloc[i]
    print(f"\n{i+1}. Artikel: {row['Artikelnummer']}")
    print(f"   Bezeichnung: {row['Bezeichnung1'][:60]}")
    print()
    print(f"   AA (Außenabmessungen - aktuell verwendet):")
    print(f"     Breite: {row.get('USER_AABreite', 'N/A')} cm")
    print(f"     Höhe:   {row.get('USER_AAHoehe', 'N/A')} cm")
    print(f"     Tiefe:  {row.get('USER_AATiefe', 'N/A')} cm")
    print()
    print(f"   AF (Abmessungen Fertig?):")
    print(f"     Breite: {row.get('USER_AFBreite', 'N/A')}")
    print(f"     Höhe:   {row.get('USER_AFHoehe', 'N/A')}")
    print(f"     Länge:  {row.get('USER_AFLaenge', 'N/A')}")
    print()
    print(f"   AI (Innenabmessungen?):")
    print(f"     Breite: {row.get('USER_AIBreite', 'N/A')}")
    print(f"     Höhe:   {row.get('USER_AIHoehe', 'N/A')}")
    print(f"     Länge:  {row.get('USER_AILaenge', 'N/A')}")

print('\n' + '='*80)
print('FAZIT:')
print('='*80)
print('Die aktuellen Werte stammen aus USER_AA* (Außenabmessungen)')
print('Dies sind die Verpackungsmaße, nicht die Produktmaße.')
print()
print('Frage an den Benutzer:')
print('  - Sollen wir USER_AA* behalten (Außenmaße der Verpackung)?')
print('  - Oder USER_AI* verwenden (vermutlich Innenmaße)?')
print('  - Oder USER_AF* verwenden (fertige Abmessungen)?')
