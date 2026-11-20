# CSR Profiles

`zh-CN/` and `en-US/` are independent CSR profile branches. Their formatting values match the corresponding CTD profiles except that both table and figure captions use Heading 1 as the chapter number and reset their sequence at level 1. This follows CSR's chapter-based structure and lets numbering restart at each chapter.

The current settings are a copied starting point, not a claim that every CSR template requires these values. Update this branch when a CSR-specific formatting requirement is confirmed, and keep the CTD profile unchanged unless that requirement also applies to CTD.

Select the locale matching the document language. Do not mix locale-specific profile settings and base templates.

Both language profiles set native heading geometry, three-line borders, 100% preferred table width, and repeatable table headers. Caption positions are configured separately under `caption.table.position` and `caption.figure.position`. Legacy table overrides, literature options, and review options are unsupported.
