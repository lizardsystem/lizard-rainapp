# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('lizard_map', '0002_auto__add_setting__add_backgroundmap'),
    )

    def forwards(self, orm):

        # Adding model 'Setting'
        db.create_table('lizard_rainapp_setting', (
            ('setting_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['lizard_map.Setting'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('lizard_rainapp', ['Setting'])


    def backwards(self, orm):

        # Deleting model 'Setting'
        db.delete_table('lizard_rainapp_setting')


    models = {
        'lizard_map.setting': {
            'Meta': {'object_name': 'Setting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'lizard_rainapp.completerainvalue': {
            'Meta': {'object_name': 'CompleteRainValue'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameterkey': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'lizard_rainapp.geoobject': {
            'Meta': {'object_name': 'GeoObject'},
            'area': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipality_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_rainapp.rainvalue': {
            'Meta': {'object_name': 'RainValue'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'geo_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_rainapp.GeoObject']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameterkey': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_rainapp.setting': {
            'Meta': {'object_name': 'Setting', '_ormbases': ['lizard_map.Setting']},
            'setting_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lizard_map.Setting']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['lizard_rainapp']
