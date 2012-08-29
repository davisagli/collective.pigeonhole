from OFS.SimpleItem import SimpleItem

from zope.interface import implements
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getUtility
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from z3c.form import field, button
from plone.z3cform.crud import crud
from plone.z3cform.layout import wrap_form
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from plone.schemaeditor.browser.schema.traversal import SchemaContext

from collective.pigeonhole.interfaces import IPigeonholeSchemaSettings
from collective.pigeonhole.interfaces import IPigeonholeSchema
from collective.pigeonhole import MessageFactory as _


class PigeonholeSchemaEditForm(crud.EditForm):
    """ Pigeonhole edit form.  Just a normal CRUD form without the form title or edit button.
    """

    label = None
    
    buttons = crud.EditForm.buttons.copy().omit('edit')
    handlers = crud.EditForm.handlers.copy()


class PigeonholeSchemaListing(crud.CrudForm):
    """ The combined pigeonhole edit + add forms.
    """
    
    @lazy_property
    def description(self):
        if self.get_items():
            return _(u'The following custom metadata schemas are available for '
                     u'your site.')
        else:
            return _(u'Click the "Add Schema" button to begin creating '
                     u' a new metadata schema.')
    
    template = ViewPageTemplateFile('schema_listing.pt')
    view_schema = field.Fields(IPigeonholeSchemaSettings).select('title', 'types', 'condition')
    addform_factory = crud.NullForm
    editform_factory = PigeonholeSchemaEditForm
    
    def _schema_collection(self):
        registry = getUtility(IRegistry)
        return registry.collectionOfInterface(IPigeonholeSchemaSettings, prefix=REGISTRY_BASE_PREFIX)

    def get_items(self):
        """ Look up all existing schemas in the registry.
        """
        return self._schema_collection().items()

    def remove(self, (name, item)):
        """ Remove a schema.
        """
        del self._schema_collection()[name]

    def link(self, item, field):
        """ Generate links to the edit page for each schema.
        """
        return '%s/%s' % (self.context.absolute_url(), item.__name__)

PigeonholeSchemaListingView = layout.wrap_form(PigeonholeSchemaListing, ControlPanelFormWrapper)
PigeonholeSchemaListingView.label = u"Pigeonhole metadata"


class PigeonholeSchemaAddForm(form.AddForm):

    label = _(u'Add Metadata Schema')
    fields = field.Fields(IPigeonholeSchema).select('title', 'name', 'types', 'condition')
    id = 'add-schema-form'

    def create(self, data):
        id = data.pop('id')

        fti = DexterityFTI(id)
        fti.id = id
        data['title'] = data['title'].encode('utf8')
        if data['description']:
            data['description'] = data['description'].encode('utf8')
        data['i18n_domain'] = 'plone'
        data['behaviors'] = "\n".join(['plone.app.dexterity.behaviors.metadata.IDublinCore',
                                       'plone.app.content.interfaces.INameFromTitle',
                                       ])
        data['model_source'] = """
<model xmlns="http://namespaces.plone.org/supermodel/schema">
    <schema>
    </schema>
</model>
"""
        if data['container']:
            data['klass'] = 'plone.dexterity.content.Container'
            data['filter_content_types'] = False
            del data['container']
            icon = 'folder_icon'
        else:
            icon = 'document_icon'
        if PLONE40:
            data['icon_expr'] = 'string:${portal_url}/' + icon + '.png'
        data['content_icon'] = icon + '.gif'
        fti.manage_changeProperties(**data)
        return fti

    def add(self, fti):
        registry = getUtility(IRegistry)
        schemas = registry.collectionOfInterface(IPigeonholeSchemaSettings, prefix=REGISTRY_BASE_PREFIX)

        registry = getUtility(IRegistry)
        schemas = registry.collectionOfInterface()
        ttool = getToolByName(self.context, 'portal_types')
        ttool._setObject(fti.id, fti)
        self.status = _(u"Schema added successfully.")

    def nextURL(self):
        return self.context.absolute_url()


class PigeonholeSchema(SchemaContext):
    implements(IPigeonholeSchemaContext)
    
    def __init__(self, name, request):
        registry = getUtility(IRegistry)
        prefix = REGISTRY_BASE_PREFIX + name
        settings = registry.forInterface(IPigeonholeSchemaSettings, prefix=prefix)
        self.context = self.schema = plone.supermodel.loadString(settings.schema_xml)

        self.request = getRequest()
        self.id = None
        self.__name__ = name
        self.Title = lambda: settings.title


class PigeonholeControlPanel(SimpleItem):
    """ This class represents the Pigeonhole configlet, and allows us to traverse
        through it to (a wrapper of) a particular schema.
    """
    implements(IBrowserPublisher)
    
    def __init__(self, context, request):
        super(PigeonholeControlPanel, self).__init__(context, request)
        
        # make sure that breadcrumbs will be correct
        self.id = None
        self.Title = lambda: _(u'Pigeonhole')
        
        # turn off green edit border for anything in the control panel
        request.set('disable_border', 1)
    
    def publishTraverse(self, request, name):
        """ 1. Try to find the schema whose name matches the next URL path element.
            2. Look up its schema.
            3. Return a schema context (an acquisition-aware wrapper of the schema).
        """
        return PigeonholeSchema(name).__of__(self)

    def browserDefault(self, request):
        """ If we aren't traversing to a schema beneath the types configlet, we actually want to
            see the PigeonholeSchemaListing.
        """
        return self, ('@@contents',)
