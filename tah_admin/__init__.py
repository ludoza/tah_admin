from flask import jsonify, make_response, current_app, g
from flask_admin.base import expose
from flask_admin.contrib import sqla

from io import BytesIO
from xml.etree import ElementTree as ET



class TahAdminViewMixin:
    @expose('/tah/err')
    def tah_err_view(self):
        raise Exception('err')
        
    @expose('/tah/list/json')
    def tah_index_view_json(self):
        count, data = self._tah_index_view()

        json_data = []
        for item in data :
            json_item = {c.name: getattr(item, c.name) for c in item.__table__.columns}
            json_data.append(json_item)
            
        return jsonify(json_data)



    @expose('/tah/list/xml')
    def tah_index_view_xml(self):
        count, data = self._tah_index_view()
        view = g.get('_admin_view')
        
        document = ET.Element('CONFIG')
        grid = ET.SubElement(document, 'grid', attrib={ 'version': '3' })
        saveoptions = ET.SubElement(grid, 'saveoptions', attrib={ 'create': "True", 'position': "False", 'content': "True"})
        design = ET.SubElement(grid, 'design')
        content = ET.SubElement(grid, 'content')
        
        cell_count = 1
        cells = ET.SubElement(content, 'cells')
        name_col = None 
        row = 1 # row 0 is header
        for item in data:
            for c in item.__table__.columns:
                if not name_col:
                    name_col = {}
                    for idx, cc in enumerate(item.__table__.columns):
                        name_col[cc.name] = idx
                        col, row, value = idx, 0, cc.name
                        cell = ET.SubElement(cells, f'cell{cell_count}' , attrib={ 'column': str(col), 'row': str(row), 'text': str(value) })
                        cell_count = cell_count + 1
                    row = row +  1

                name, value = c.name, getattr(item, c.name)
                col = name_col[name]
                cell = ET.SubElement(cells, f'cell{cell_count}' , attrib={ 'column': str(col), 'row': str(row), 'text': str(value) })
                cell_count = cell_count + 1
            row = row + 1    
        cells.attrib['cellcount'] = str(cell_count)
        design.attrib['rowcount'] = str(row)
        
        et = ET.ElementTree(document)        
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True) 
        return make_response(f.getvalue())


    def _tah_index_view(self):
        """
            List view
        """
        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get page size
        page_size = view_args.page_size or self.page_size

        # Get count and data
        count, data = self.get_list(view_args.page, sort_column, view_args.sort_desc,
                                    view_args.search, view_args.filters, page_size=page_size)
        return count, data



class TahModelView(TahAdminViewMixin, sqla.ModelView):
    pass
