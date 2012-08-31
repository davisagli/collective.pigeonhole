from zope.site.hooks import getSite
from zope.schema.interfaces import IList, IChoice
from Products.CMFCore.utils import getToolByName


def handle_field_added(ph_schema, event):
    field = event.field
    index_name = ph_schema.__name__ + '.' + field.__name__
    catalog = getToolByName(getSite(), 'portal_catalog')
    if index_name not in catalog.Indexes:
        if IList.providedBy(field) and IChoice.providedBy(field.value_type):
            catalog.addIndex(index_name, 'KeywordIndex')
        if IChoice.providedBy(field):
            catalog.addIndex(index_name, 'FieldIndex')


def handle_field_removed(ph_schema, event):
    field = event.field
    index_name = ph_schema.__name__ + '.' + field.__name__
    catalog = getToolByName(getSite(), 'portal_catalog')
    if index_name in catalog.Indexes:
        catalog.removeIndex(index_name)
