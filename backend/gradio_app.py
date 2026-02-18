import sqlite3
import os
import gradio as gr

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

def search_html(q: str):
    q = (q or '').strip()
    if not q:
        return '<div>No query provided.</div>'
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        sql = "SELECT product_name, company_name, seller_contact, website, catalogue_link, description FROM products_fts WHERE products_fts MATCH ? LIMIT 200"
        cur.execute(sql, (q,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return f'<div style="color: #666;">No results found for: <strong>{q}</strong></div>'

        parts = [f'<div><strong>Results ({len(rows)}):</strong></div><ul>']
        for r in rows:
            product_name, company_name, seller_contact, website, catalogue_link, description = r
            parts.append('<li>')
            parts.append(f'<strong>{product_name}</strong> — {company_name}<br>')
            parts.append(f'Contact: {seller_contact} | Website: <a href="{website}" target="_blank">{website}</a><br>')
            parts.append(f'Description: {description}<br>')
            if catalogue_link:
                parts.append(f'Catalogue: <a href="{catalogue_link}" target="_blank">Open Catalogue</a>')
            parts.append('</li>')
        parts.append('</ul>')
        return '\n'.join(parts)
    except Exception as e:
        return f'<div style="color: red;">Error: {str(e)}</div>'

def main():
    with gr.Blocks(title='Product Search (Gradio)') as demo:
        gr.Markdown('# Product Search')
        txt = gr.Textbox(label='Query', placeholder='Enter product meta word (e.g., ghee)')
        out = gr.HTML()
        btn = gr.Button('Search')
        btn.click(lambda q: search_html(q), inputs=txt, outputs=out)
        txt.submit(lambda q: search_html(q), inputs=txt, outputs=out)

    demo.launch(server_name='0.0.0.0', share=False)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print('Database not found — run init_db.py first to create', DB_PATH)
    main()
