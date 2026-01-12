"""Selection rectangle utilities for UI components."""

def create_selection_rect(canvas, x1, y1, size, fill='', outline='', callback=None):
    """Create a selection rectangle with hit area and callback"""
    # Create visible rectangle
    rect_id = canvas.create_rectangle(x1, y1, x1 + size, y1 + size, fill=fill, outline=outline)
    
    # Create larger invisible hit area
    hit_id = canvas.create_rectangle(x1 - 5, y1 - 5, x1 + size + 5, y1 + size + 5, 
                                   fill='', outline='', state='hidden')
    
    # Bind click event to callback
    if callback:
        canvas.tag_bind(hit_id, '<Button-1>', lambda e: callback())
        canvas.tag_bind(rect_id, '<Button-1>', lambda e: callback())
    
    return rect_id, hit_id