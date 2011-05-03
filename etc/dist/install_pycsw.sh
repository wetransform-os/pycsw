#!/bin/sh
# Copyright (c) 2011 The Open Source Geospatial Foundation.
# Licensed under the GNU LGPL.
# 
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 2.1 of the License,
# or any later version.  This library is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY, without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details, either
# in the "LICENSE.LGPL.txt" file distributed with this software or at
# web page "http://www.fsf.org/licenses/lgpl.html".

# About:
# =====
# This script will install pycsw

# Running:
# =======
# sudo ./install_pycsw.sh

# Requires: Apache2, python-lxml, python-shapely and python-sqlalchemy
#
# Uninstall:
# ============
# sudo rm /etc/apache2/conf.d/pycsw
# sudo rm -rf /var/www/pycsw*

VERSION=0.2.0-dev

echo -n 'Installing pycsw $VERSION'

echo -n 'Installing dependencies ...'

# install dependencies
apt-get install apache2 python-lxml python-sqlalchemy python-shapely

# live disc's username is "user"
USER_NAME=user
USER_HOME=/home/$USER_NAME

WEB=/var/www

# package specific settings
PYCSW_HOME=$WEB/pycsw
PYCSW_TMP=/tmp/build_pycsw
PYCSW_APACHE_CONF=/etc/apache2/conf.d/pycsw

mkdir -p "$PYCSW_TMP"

echo -n 'Downloading package ...'

# Download pycsw LiveDVD tarball.
wget -N --progress=dot:mega "https://sourceforge.net/projects/pycsw/files/$VERSION/pycsw-$VERSION.tar.gz/download" \
     -O "$PYCSW_TMP/pycsw-$VERSION.tar.gz"

echo -n 'Extracting package ...'

# Uncompress pycsw LiveDVD tarball.
tar -zxvf "$PYCSW_TMP/pycsw-$VERSION.tar.gz" -C "$PYCSW_TMP"
mv "$PYCSW_TMP/pycsw-$VERSION" "$PYCSW_TMP/pycsw"
mv "$PYCSW_TMP/pycsw" $WEB

echo -n "Updating Apache configuration ..."
# Add pycsw apache configuration
cat << EOF > "$PYCSW_APACHE_CONF"

        <Directory $PYCSW_HOME>
	    Options FollowSymLinks +ExecCGI
	    Allow from all
	    AddHandler cgi-script .py
        </Directory>

EOF

echo -n "Generating configuration files ..."
# Add pycsw configuration files

cat << EOF > $PYCSW_HOME/default.cfg

[server]
home=/var/www/pycsw
url=http://localhost/pycsw/csw.py
mimetype=application/xml; charset=iso-8859-1
encoding=iso-8859-1
language=en-CA
maxrecords=10
#loglevel=DEBUG
#logfile=/tmp/pycsw.log
#ogc_schemas_base=http://foo
#federatedcatalogues=http://geodiscover.cgdi.ca/wes/serviceManagerCSW/csw
xml_pretty_print=true
#gzip_compresslevel=8
transactions=false
transactions_ips=127.0.0.1
#profiles=apiso

[metadata]
identification_title=pycsw Geospatial Catalogue
identification_abstract=pycsw is an OGC CSW server implementation written in Python
identification_keywords=catalogue,discovery
identification_fees=None
identification_accessconstraints=None
provider_name=pycsw
provider_url=http://pycsw.org/
contact_name=Kralidis, Tom
contact_position=Senior Systems Scientist
contact_address=TBA
contact_city=Toronto
contact_stateorprovince=Ontario
contact_postalcode=M9C 3Z9
contact_country=Canada
contact_phone=+01-416-xxx-xxxx
contact_fax=+01-416-xxx-xxxx
contact_email=tomkralidis@hotmail.com
contact_url=http://www.kralidis.ca/
contact_hours=0800h - 1600h EST
contact_instructions=During hours of service.  Off on weekends.
contact_role=pointOfContact

[repository:cite]
typename=csw:Record
enabled=true
database=sqlite:////var/www/pycsw/data/cite/dc.db
table=records
cq_dc_title=title
cq_dc_creator=creator
cq_dc_subject=subject
cq_dct_abstract=abstract
cq_dc_publisher=publisher
cq_dc_contributor=contributor
cq_dct_modified=modified
cq_dc_date=date
cq_dc_type=type
cq_dc_format=format
cq_dc_identifier=identifier
cq_dc_source=source
cq_dc_language=language
cq_dc_relation=relation
cq_ows_BoundingBox=bbox
cq_dc_rights=rights
cq_csw_AnyText=csw_anytext

[repository:iso_records]
enabled=true
typename=gmd:MD_Metadata
database=sqlite:////var/www/pycsw/trunk/server/profiles/apiso/data/apiso.db
table=md_metadata
cq_name=SupportedIsoQueryables
cq_apiso_Subject=subject
cq_apiso_Title=title
cq_apiso_Abstract=abstract
cq_apiso_Format=format
cq_apiso_Identifier=resource_identifier
cq_apiso_Modified=date
cq_apiso_Type=type
cq_apiso_BoundingBox=bbox
cq_apiso_CRS=crs
cq_apiso_RevisionDate=revision_date
cq_apiso_AlternateTitle=alternate_title
cq_apiso_CreationDate=creation_date
cq_apiso_PublicationDate=publication_date
cq_apiso_OrganisationName=organisation_name
cq_apiso_HasSecurityConstraints=conditions_access_use
cq_apiso_Language=language
cq_apiso_ParentIdentifier=parent_identifier
cq_apiso_KeywordType=keyword_type
cq_apiso_TopicCategory=topic_category
cq_apiso_ResourceLanguage=resource_language
cq_apiso_GeographicDescriptionCode=geographic_description_code
cq_apiso_Denominator=scale_denominator
cq_apiso_DistanceValue=distance_value
cq_apiso_DistanceUOM=distance_unit
cq_apiso_TempExtent_begin=temporal_extent_begin
cq_apiso_TempExtent_end=temporal_extent_end
cq_apiso_AnyText=csw_anytext
cq_apiso_ServiceType=service_type
cq_apiso_ServiceTypeVersion=service_type_version
cq_apiso_Operation=operation
cq_apiso_CouplingType=coupling_type
cq_apiso_OperatesOn=operates_on
cq_apiso_OperatesOnIdentifier=operates_on_identifier
cq_apiso_OperatesOnName=operates_on_name

aq_name=AdditionalQueryables
aq_apiso_Degree=degree
aq_apiso_AccessConstraints=access_constraints
aq_apiso_OtherConstraints=other_constraints
aq_apiso_Classification=classification
aq_apiso_ConditionApplyingToAccessAndUse=conditions_access_use
aq_apiso_Lineage=lineage
aq_apiso_ResponsiblePartyRole=responsible_party_role
aq_apiso_SpecificationTitle=specification_title
aq_apiso_SpecificationDate=specification_date
aq_apiso_SpecificationDateType=specification_date_type

EOF

echo -n "Done\n"

#Add Launch icon to desktop
if [ ! -e /usr/share/applications/pycsw.desktop ] ; then
   cat << EOF > /usr/share/applications/pycsw.desktop
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name=pycsw
Comment=pycsw catalog server
Categories=Application;Education;Geography;
Exec=firefox http://localhost/pycsw/tester/index.html
Icon=
Terminal=false
StartupNotify=false
Categories=Education;Geography;
EOF
fi
cp /usr/share/applications/pycsw.desktop "$USER_HOME/Desktop/"
chown "$USER_NAME:$USER_NAME" "$USER_HOME/Desktop/pycsw.desktop"

# Reload Apache
/etc/init.d/apache2 force-reload