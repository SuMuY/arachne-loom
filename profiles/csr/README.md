# CSR Profiles

`zh-CN/` and `en-US/` are independent CSR profile branches. Their formatting values currently match the corresponding CTD profiles exactly; only the profile identity (`configId`) and schema identity are CSR-specific. This gives CSR a separate configuration that can evolve without changing CTD.

The current settings are a copied starting point, not a claim that every CSR template requires these values. Update this branch when a CSR-specific formatting requirement is confirmed, and keep the CTD profile unchanged unless that requirement also applies to CTD.

Select the locale matching the document language. Do not mix locale-specific profile settings and base templates.
