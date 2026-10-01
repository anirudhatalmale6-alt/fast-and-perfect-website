# Social media image kit

Ready-to-upload profile and cover images, generated from
`site/assets/img/logo.png`.

| File | Where it goes | Size |
|---|---|---|
| `profile-picture-1000x1000.png` | Facebook, Instagram, TikTok, Google profile picture | 1000 x 1000 |
| `facebook-cover-1640x624.png` | Facebook page cover | 1640 x 624 |
| `google-logo-720x720.png` | Google Business Profile logo | 720 x 720 |
| `google-cover-1024x575.png` | Google Business Profile cover | 1024 x 575 |
| `kijiji-listing-1200x900.png` | Kijiji, first photo on the ad | 1200 x 900 |
| `social-image-kit-guide.png` | Reference sheet showing how each one crops | |

## Two things that drove the design

**Every platform masks profile pictures to a circle.** The logo is 2.5:1,
so dropped in at full width the circle cuts off "FAST" at one end and "LTD"
at the other. For a logo of width `w` and aspect `ar`, the corners only fit
inside a circle of radius `r` when `w <= 2*sqrt(r^2/(1+ar^2))`. At
1000x1000 that is 929px; these use ~780px so the padding looks deliberate.

**Navy, not white.** The "CLEANING SERVICES" line in the logo is white and
vanishes on a white background. Both were rendered and compared.

**Facebook crops covers on mobile** to roughly the central 1109px of the
1640px width. The logo, tagline, phone number and URL all sit inside that
band, so nothing important is lost on a phone.

To regenerate after a logo change, the sizes above are the targets; keep the
profile picture at or under 929px of logo width on a 1000px canvas.
