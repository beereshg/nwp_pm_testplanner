"""
Shared Intel-blue card HTML styles for HSD description enrichment.

Usage in generator scripts:
    from hsd_utils.html_styles import card, body, codeblk, th, tr, INFO, WARN
"""

CARD = 'background:rgb(0,113,197);color:white;padding:8px 14px;border-radius:6px 6px 0 0;font-weight:bold;font-size:13px'
BODY = 'background:white;margin-bottom:16px;border:1px solid #c8c8c8;border-top:none;padding:12px 14px;font-family:Calibri,sans-serif;font-size:13px;line-height:1.5'
CODE = 'background:#f4f4f4;border:1px solid #ddd;border-radius:4px;padding:10px;font-family:Consolas,monospace;font-size:12px;white-space:pre;display:block;margin:8px 0'
INFO = 'background:#d1ecf1;border-left:4px solid #17a2b8;padding:8px 12px;margin:8px 0;font-size:12px'
WARN = 'background:#fff3cd;border-left:4px solid #ffc107;padding:8px 12px;margin:8px 0;font-size:12px'
OK   = 'background:#d4edda;border-left:4px solid #28a745;padding:8px 12px;margin:8px 0;font-size:12px'
TBL  = 'border:1px solid #ccc;padding:5px 8px;font-size:12px'
TH   = 'border:1px solid #ccc;padding:5px 8px;font-size:12px;background:#f0f0f0;font-weight:bold'


def card(t: str) -> str:
    return f'<div style="{CARD}">{t}</div>\n'


def body(t: str) -> str:
    return f'<div style="{BODY}">{t}</div>\n'


def info(t: str) -> str:
    return f'<div style="{INFO}">{t}</div>'


def warn(t: str) -> str:
    return f'<div style="{WARN}">{t}</div>'


def ok_banner(t: str) -> str:
    return f'<div style="{OK}">{t}</div>'


def codeblk(t: str) -> str:
    safe = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f'<div style="{CODE}">{safe}</div>'


def th(*cols) -> str:
    return '<tr>' + ''.join(f'<th style="{TH}">{c}</th>' for c in cols) + '</tr>'


def tr(*cols) -> str:
    return '<tr>' + ''.join(f'<td style="{TBL}">{c}</td>' for c in cols) + '</tr>'


def table(*rows: str, style: str = 'border-collapse:collapse;width:100%;margin-top:6px') -> str:
    return f'<table style="{style}">{"".join(rows)}</table>'
