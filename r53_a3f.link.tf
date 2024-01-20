
resource "aws_route53_zone" "a3f_link" {
  name = "a3f.link"
}


module "r53_ingress_lb_a3f_link" {
  source  = "./modules/route53_record"
  zone_id = aws_route53_zone.a3f_link.zone_id
  name    = "ingress-lb.a3f.link."
  type    = "A"
  # records = [module.servarr_ingress.ip_address]
  records    = ["192.168.11.86"]
  depends_on = [aws_route53_zone.a3f_link]
}


module "r53_dashboard_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "dashboard.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link]
}


module "r53_books_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "books.a3f.link."
  type       = "A"
  records    = ["192.168.11.88"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_radarr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "radarr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_sonarr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "sonarr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_readarr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "readarr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_lazylibrarian_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "lazylibrarian.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_prowlarr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "prowlarr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_bazarr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "bazarr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_overseerr_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "overseerr.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_tautulli_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "tautulli.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_htpcmanager_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "htpcmanager.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_muximux_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "muximux.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_plexmetamanager_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "plexmetamanager.a3f.link."
  type       = "CNAME"
  records    = ["${module.r53_ingress_lb_a3f_link.fqdn}."]
  depends_on = [aws_route53_zone.a3f_link, module.r53_ingress_lb_a3f_link]
}

module "r53_b5bc_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b5bc.a3f.link."
  type       = "A"
  records    = ["192.168.11.109"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_b762_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b762.a3f.link."
  type       = "A"
  records    = ["192.168.11.243"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_b852_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b852.a3f.link."
  type       = "A"
  records    = ["192.168.11.129"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_b8b9_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b8b9.a3f.link."
  type       = "A"
  records    = ["192.168.11.193"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_b983_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b983.a3f.link."
  type       = "A"
  records    = ["192.168.11.23"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_b9a5_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "b9a5.a3f.link."
  type       = "A"
  records    = ["192.168.11.57"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_fd0e_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "fd0e.a3f.link."
  type       = "A"
  records    = ["192.168.11.242"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_pihole_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "pihole.a3f.link."
  type       = "A"
  records    = ["192.168.11.81"]
  depends_on = [aws_route53_zone.a3f_link]
}

module "r53_nzbget_a3f_link" {
  source     = "./modules/route53_record"
  zone_id    = aws_route53_zone.a3f_link.zone_id
  name       = "nzbget.a3f.link."
  type       = "A"
  records    = ["192.168.11.71"]
  depends_on = [aws_route53_zone.a3f_link]
}

