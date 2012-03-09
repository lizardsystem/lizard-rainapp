# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'GeoObject'
        db.create_table('lizard_rainapp_geoobject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('municipality_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=16, null=True)),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('y', self.gf('django.db.models.fields.FloatField')()),
            ('area', self.gf('django.db.models.fields.FloatField')()),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.GeometryField')()),
        ))
        db.send_create_signal('lizard_rainapp', ['GeoObject'])

        # Adding model 'RainValue'
        db.create_table('lizard_rainapp_rainvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('geo_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_rainapp.GeoObject'])),
            ('parameterkey', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('lizard_rainapp', ['RainValue'])

        # Adding model 'CompleteRainValue'
        db.create_table('lizard_rainapp_completerainvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parameterkey', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('lizard_rainapp', ['CompleteRainValue'])


    def backwards(self, orm):

        # Deleting model 'GeoObject'
        db.delete_table('lizard_rainapp_geoobject')

        # Deleting model 'RainValue'
        db.delete_table('lizard_rainapp_rainvalue')

        # Deleting model 'CompleteRainValue'
        db.delete_table('lizard_rainapp_completerainvalue')


    models = {
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
        }
    }

    complete_apps = ['lizard_rainapp']
