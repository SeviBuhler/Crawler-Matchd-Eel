def get_crawler_method(url):
    """Get the appropriate crawler method for a URL"""
    
    url_mappings = {
        'benedict.ch': lambda: _get_benedict_crawler(),
        'vantage.ch': lambda: _get_vantage_crawler(),
        'bzwu.ch': lambda: _get_bzwu_crawler(),
        'ffhs.ch': lambda: _get_ffhs_crawler(),
        'fhgr.ch': lambda: _get_fhgr_crawler(),
        'recruitingapp-2800.umantis.com': lambda: _get_ktsg_crawler(),
        'ipso.ch': lambda: _get_ipso_crawler(),
        'phsg.ch': lambda: _get_phsg_crawler(),
        'ohws.prospective.ch/public/v1/medium/1007649/': lambda: _get_ost_crawler(),
        'www.swissengineering.ch/api/de/jobs': lambda: _get_swissengineering_crawler(),
        'startfeld.jobportal.jobchannel.ch/search': lambda: _get_startfeld_crawler(),
        'rheintalcom.jobportal.jobchannel.ch/search': lambda: _get_rheintalcom_crawler(),
        'digitalliechtenstein.jobportal.jobchannel.ch/search': lambda: _get_digitalliechtenstein_crawler(),
        'eastdigital.jobportal.jobchannel.ch/search': lambda: _get_eastdigital_crawler(),
        'jobs.inside-it.ch/jobs/': lambda: _get_insideit_crawler(),
        'api.jobportal.abaservices.ch/api/application/publication/abacusjobs/0': lambda: _get_abacus_crawler(),
        'live.solique.ch/STSG/de/api/v1/data/': lambda: _get_stsg_crawler(),
        'www.valantic.com/de/karriere/': lambda: _get_valantic_crawler(),
        'www.abraxas.ch/de/karriere/offene-stellen': lambda: _get_abraxas_crawler(),
        'ohws.prospective.ch/public/v1/medium/1008005/': lambda: _get_buehler_crawler(),
        'jobs.dualoo.com/portal/lx0anfq4?lang=DE': lambda: _get_egeli_crawler(),
        'jobs.h-och.ch/search/': lambda: _get_hoch_crawler(),
        'inventx.onlyfy.jobs/candidate/job/ajax_list?display_length=40': lambda: _get_inventx_crawler(),
        'kms-ag.ch/karriere/offene-jobs/': lambda: _get_kms_crawler(),
        'infosystem.ch/karriere': lambda: _get_infosystem_crawler(),
        'hexagon.com/company/careers/job-listings': lambda: _get_hexagon_crawler(),
        'ohws.prospective.ch/public/v1/medium/1950/': lambda: _get_raiffeisen_crawler(),
        'join.sfs.com/ch/en/vacancies/index.jsp': lambda: _get_sfs_crawler(),
        'recruitingapp-9300.umantis.com/Jobs/All': lambda: _get_umantis_crawler(),
        'acreo.ch/unternehmen': lambda: _get_acreo_crawler(),
        'all-consulting.ch/de/uber-uns/karriere/aktuelle-stellen': lambda: _get_allconsulting_crawler(),
        'aproda.ch/ueber-uns/karriere/offene-stellen': lambda: _get_aproda_crawler(),
        'zootsolutions.eu/de/career/': lambda: _get_zootsolutions_crawler(),
        'stackworks.ch/karriere#jobs': lambda: _get_stackworks_crawler(),
        'optisizer.ch/jobs': lambda: _get_optisizer_crawler(),
        'ari-ag.ch/jobs-karriere/offene-stellen/': lambda: _get_ari_crawler(),
        'nextlevelconsulting.com/karriere/#jobs': lambda: _get_nextlevelconsulting_crawler(),
        'edorex.ch/jobs/': lambda: _get_edorex_crawler(),
        'diselva.com/de/jobs': lambda: _get_diselva_crawler(),
        'app.ch/karriere/stellenangebote': lambda: _get_app_crawler(),
        'advision.swiss/karriere/': lambda: _get_advision_crawler(),
        'xerxes.ch/stellen': lambda: _get_xerxes_crawler(),
        'webwirkung.ch/karriere/': lambda: _get_webwirkung_crawler(),
        'stgallennetgroup.ch/unternehmen/jobs/': lambda: _get_stgallennetgroup_crawler(),
        'robotron.ch/karriere': lambda: _get_robotron_crawler(),
        'joshmartin.ch/stellen/': lambda: _get_joshmartin_crawler(),
        'farner.ch/de/jobs/': lambda: _get_farner_crawler(),
        'dynanet.ch/jobs/': lambda: _get_dynanet_crawler(),
        'dachcom.com/de-ch/agentur/karriere': lambda: _get_dachcom_crawler(),
        'adesso.ch/de_ch/jobs-karriere/unsere-stellenangebote/stellenangebote.html': lambda: _get_adesso_crawler(),
        'jobs.unisg.ch': lambda: _get_unisg_crawler(),
        'svasg-jobs.abacuscity.ch/de/jobportal/': lambda: _get_svasg_crawler(),
        'sgkb.ch/de/ueber-uns/karriere/stellenangebote': lambda: _get_sgkb_crawler(),
        'karriere.sak.ch/go/SAK-Jobs/9138055/': lambda: _get_sak_crawler(),
        'ohws.prospective.ch/public/v1/careercenter/1005765/': lambda: _get_psychiatriesg_crawler(),
        'jobs.dualoo.com/portal/ppqp7jqv?lang=DE': lambda: _get_permapack_crawler(),
        'jobs.dualoo.com/portal/761twmr4?lang=DE': lambda: _get_permapack_crawler(),
        'jobs.dualoo.com/portal/4tgi9rpu?lang=DE': lambda: _get_permapack_crawler(),
        'optimatik.ch/jobs': lambda: _get_optimatik_crawler(),
        'oertli-jobs.com/stellenangebote.html': lambda: _get_oertli_crawler(),
        'obt.ch/de/karriere/offene-stellen': lambda: _get_obt_crawler(),
        'netsafe.ch/jobs': lambda: _get_netsafe_crawler(),
        'neovac.ch/jobs': lambda: _get_neovac_crawler(),
        'jobs.mtf.ch/de/jobportal': lambda: _get_mtf_crawler(),
        'msdirectgroup-jobs.abacuscity.ch/de/jobportal': lambda: _get_msdirect_crawler(),
        'search-api.metrohm.com/search': lambda: _get_metrohm_crawler(),
        'merkle.com/en/careers.jobs.js?offset=24&limit=400': lambda: _get_merkle_crawler(),
        'management.ostjob.ch/minisite/62': lambda: _get_kellenberger_crawler(),
        'jobs.dualoo.com/portal/elj8aw7v': lambda: _get_laveba_crawler(),
        'join.com/companies/emonitor': lambda: _get_emonitor_crawler(),
    }
    
    for domain, crawler_loader in url_mappings.items():
        if domain in url:
            return crawler_loader()
    
    return None

def _get_benedict_crawler():
    from .crawlMethods.benedict import crawl_benedict
    return crawl_benedict

def _get_vantage_crawler():
    from .crawlMethods.vantage import crawl_vantage
    return crawl_vantage

def _get_bzwu_crawler():
    from .crawlMethods.bzwu import crawl_bzwu
    return crawl_bzwu

def _get_ffhs_crawler():
    from .crawlMethods.ffhs import crawl_ffhs
    return crawl_ffhs

def _get_fhgr_crawler():
    from .crawlMethods.fhgr import crawl_fhgr
    return crawl_fhgr

def _get_ktsg_crawler():
    from .crawlMethods.ktsg import crawl_ktsg
    return crawl_ktsg

def _get_ipso_crawler():
    from .crawlMethods.ipso import crawl_ipso
    return crawl_ipso

def _get_phsg_crawler():
    from .crawlMethods.phsg import crawl_phsg
    return crawl_phsg

def _get_ost_crawler():
    from .crawlMethods.ost import crawl_ost
    return crawl_ost

def _get_swissengineering_crawler():
    from .crawlMethods.swissengineering import crawl_swissengineering
    return crawl_swissengineering

def _get_startfeld_crawler():
    from .crawlMethods.startfeld import crawl_startfeld
    return crawl_startfeld

def _get_rheintalcom_crawler():
    from .crawlMethods.rheintalcom import crawl_rheintalcom
    return crawl_rheintalcom

def _get_digitalliechtenstein_crawler():
    from .crawlMethods.digitalliechtenstein import crawl_digitalliechtenstein
    return crawl_digitalliechtenstein

def _get_eastdigital_crawler():
    from .crawlMethods.eastdigital import crawl_eastdigital
    return crawl_eastdigital

def _get_insideit_crawler():
    from .crawlMethods.insideit import crawl_insideit
    return crawl_insideit

def _get_abacus_crawler():
    from .crawlMethods.abacus import crawl_abacus
    return crawl_abacus

def _get_stsg_crawler():
    from .crawlMethods.stsg import crawl_stsg
    return crawl_stsg

def _get_valantic_crawler():
    from .crawlMethods.valantic import crawl_valantic
    return crawl_valantic

def _get_abraxas_crawler():
    from .crawlMethods.abraxas import crawl_abraxas
    return crawl_abraxas

def _get_buehler_crawler():
    from .crawlMethods.buehler import crawl_buehler
    return crawl_buehler

def _get_egeli_crawler():
    from .crawlMethods.egeli import crawl_egeli
    return crawl_egeli

def _get_hoch_crawler():
    from .crawlMethods.hoch import crawl_hoch
    return crawl_hoch

def _get_inventx_crawler():
    from .crawlMethods.inventx import crawl_inventx
    return crawl_inventx

def _get_kms_crawler():
    from .crawlMethods.kms import crawl_kms
    return crawl_kms

def _get_infosystem_crawler():
    from .crawlMethods.infosystem import crawl_infosystem
    return crawl_infosystem

def _get_hexagon_crawler():
    from .crawlMethods.hexagon import crawl_hexagon
    return crawl_hexagon

def _get_raiffeisen_crawler():
    from .crawlMethods.raiffeisen import crawl_raiffeisen
    return crawl_raiffeisen

def _get_sfs_crawler():
    from .crawlMethods.sfs import crawl_sfs
    return crawl_sfs

def _get_umantis_crawler():
    from .crawlMethods.umantis import crawl_umantis
    return crawl_umantis

def _get_acreo_crawler():
    from .crawlMethods.acreo import crawl_acreo
    return crawl_acreo

def _get_allconsulting_crawler():
    from .crawlMethods.allconsulting import crawl_allconsulting
    return crawl_allconsulting

def _get_aproda_crawler():
    from .crawlMethods.aproda import crawl_aproda
    return crawl_aproda

def _get_zootsolutions_crawler():
    from .crawlMethods.zootsolutions import crawl_zootsolutions
    return crawl_zootsolutions

def _get_stackworks_crawler():
    from .crawlMethods.stackworks import crawl_stackworks
    return crawl_stackworks

def _get_optisizer_crawler():
    from .crawlMethods.optisizer import crawl_optisizer
    return crawl_optisizer

def _get_ari_crawler():
    from .crawlMethods.ari import crawl_ari
    return crawl_ari

def _get_nextlevelconsulting_crawler():
    from .crawlMethods.nextlevelconsulting import crawl_nextlevelconsulting
    return crawl_nextlevelconsulting

def _get_edorex_crawler():
    from .crawlMethods.edorex import crawl_edorex
    return crawl_edorex

def _get_diselva_crawler():
    from .crawlMethods.diselva import crawl_diselva
    return crawl_diselva

def _get_app_crawler():
    from .crawlMethods.app import crawl_app
    return crawl_app

def _get_advision_crawler():
    from .crawlMethods.advision import crawl_advision
    return crawl_advision

def _get_xerxes_crawler():
    from .crawlMethods.xerxes import crawl_xerxes
    return crawl_xerxes

def _get_webwirkung_crawler():
    from .crawlMethods.webwirkung import crawl_webwirkung
    return crawl_webwirkung

def _get_stgallennetgroup_crawler():
    from .crawlMethods.stgallennetgroup import crawl_stgallennetgroup
    return crawl_stgallennetgroup

def _get_robotron_crawler():
    from .crawlMethods.robotron import crawl_robotron
    return crawl_robotron

def _get_joshmartin_crawler():
    from .crawlMethods.joshmartin import crawl_joshmartin
    return crawl_joshmartin

def _get_farner_crawler():
    from .crawlMethods.farner import crawl_farner
    return crawl_farner

def _get_dynanet_crawler():
    from .crawlMethods.dynanet import crawl_dynanet
    return crawl_dynanet

def _get_dachcom_crawler():
    from .crawlMethods.dachcom import crawl_dachcom
    return crawl_dachcom

def _get_adesso_crawler():
    from .crawlMethods.adesso import crawl_adesso
    return crawl_adesso

def _get_unisg_crawler():
    from .crawlMethods.unisg import crawl_unisg
    return crawl_unisg

def _get_svasg_crawler():
    from .crawlMethods.svasg import crawl_svasg
    return crawl_svasg

def _get_sgkb_crawler():
    from .crawlMethods.sgkb import crawl_sgkb
    return crawl_sgkb

def _get_sak_crawler():
    from .crawlMethods.sak import crawl_sak
    return crawl_sak

def _get_psychiatriesg_crawler():
    from .crawlMethods.psychiatriesg import crawl_psychiatriesg
    return crawl_psychiatriesg

def _get_permapack_crawler():
    from .crawlMethods.permapack import crawl_permapack
    return crawl_permapack

def _get_optimatik_crawler():
    from .crawlMethods.optimatik import crawl_optimatik
    return crawl_optimatik

def _get_oertli_crawler():
    from .crawlMethods.oertli import crawl_oertli
    return crawl_oertli

def _get_obt_crawler():
    from .crawlMethods.obt import crawl_obt
    return crawl_obt

def _get_netsafe_crawler():
    from .crawlMethods.netsafe import crawl_netsafe
    return crawl_netsafe

def _get_neovac_crawler():
    from .crawlMethods.neovac import crawl_neovac
    return crawl_neovac

def _get_mtf_crawler():
    from .crawlMethods.mtf import crawl_mtf
    return crawl_mtf

def _get_msdirect_crawler():
    from .crawlMethods.msdirect import crawl_msdirect
    return crawl_msdirect

def _get_metrohm_crawler():
    from .crawlMethods.metrohm import crawl_metrohm
    return crawl_metrohm

def _get_merkle_crawler():
    from .crawlMethods.merkle import crawl_merkle
    return crawl_merkle

def _get_kellenberger_crawler():
    from .crawlMethods.kellenberger import crawl_kellenberger
    return crawl_kellenberger

def _get_laveba_crawler():
    from .crawlMethods.laveba import crawl_laveba
    return crawl_laveba

def _get_emonitor_crawler():
    from .crawlMethods.emonitor import crawl_emonitor
    return crawl_emonitor