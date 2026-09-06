from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from company.models import Company

from master.models import (
    JewelryCategory, JewelrySubCategory, MetalPurity,
    FindingType, Setting, FinishType,
)
from properties.models import (
    DiamondStone, DiamondShape, DiamondSize, DiamondColor, DiamondCut, DiamondQuality, DiamondStoneRate,
    ColorStone, ColorStoneShape, ColorStoneSize, ColorStoneColor, ColorStoneCut, ColorStoneQuality, ColorStoneRate,
)


def front_view_image(instance, filename):
    return f"cards/costs/{instance.pk or 'new'}/front/{filename}"


def side_view_image(instance, filename):
    return f"cards/costs/{instance.pk or 'new'}/side/{filename}"


def back_view_image(instance, filename):
    return f"cards/costs/{instance.pk or 'new'}/back/{filename}"


class CardsFieldsMixin(models.Model):
    """Common fields for cards tables (mirrors master.MasterFieldsMixin)."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'), help_text=_('Date and time when this record was created.'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'), help_text=_('Date and time when this record was last updated.'))
    active = models.BooleanField(default=True, verbose_name=_('Active'), help_text=_('Whether this record is currently active.'))

    class Meta:
        abstract = True


class StonePlace(CardsFieldsMixin):
    """Where a stone sits on the piece (e.g. Center, Side, Halo)."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'), help_text=_('Name of the stone placement.'))
    description = models.CharField(max_length=250, null=True, blank=True, verbose_name=_('Description'), help_text=_('Optional description of the stone placement.'))

    class Meta:
        verbose_name = _('Stone Place')
        verbose_name_plural = _('Stone Places')
        ordering = ['name']
        indexes = [
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return self.name


class CostCard(CardsFieldsMixin):
    # ---- General tab ----
    cost_card_no = models.CharField(max_length=50, unique=True, verbose_name=_('Cost Card No'), help_text=_('Auto-generated identifier for this cost card.'))
    our_style_no = models.CharField(max_length=100, verbose_name=_('Our Style No'), help_text=_('Style number used internally to identify this jewelry piece.'))
    vendor_style_no = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('Vendor Style No'), help_text=_("Style number used by the vendor for this piece."))
    vendor = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards_as_vendor', verbose_name=_('Vendor'), help_text=_('Vendor this cost card is raised against.'))
    customer = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards_as_customer', verbose_name=_('Customer'), help_text=_('Customer this cost card is prepared for.'))
    category = models.ForeignKey(JewelryCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards', verbose_name=_('Jewelry Category'), help_text=_('Jewelry category of this piece.'))
    sub_category = models.ForeignKey(JewelrySubCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards', verbose_name=_('Jewelry Sub Category'), help_text=_('Jewelry sub-category of this piece.'))
    metal_purity = models.ForeignKey(MetalPurity, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards', verbose_name=_('Metal Purity'), help_text=_('Metal purity grade used for this piece.'))
    karat = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('Kt'), help_text=_('Karat value of the metal, e.g. 14KT, 18KT.'))
    metal_grams = models.DecimalField(max_digits=10, decimal_places=3, verbose_name=_('Metal Grams'), help_text=_('Weight of metal used, in grams.'))
    finding_type = models.ForeignKey(FindingType, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_cards', verbose_name=_('Finding Type'), help_text=_('Finding type used on this piece.'))
    finding_price = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Finding Price'), help_text=_('Price charged for the finding used.'))
    gross_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name=_('Gross Weight'), help_text=_('Total gross weight of the piece.'))
    net_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name=_('Net Weight'), help_text=_('Net weight of the piece excluding stones.'))
    troy_ounce_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name=_('Troy Ounce Price'), help_text=_('Metal price per troy ounce, frozen at the time of costing.'))

    height_mm = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Height MM'), help_text=_('Height of the piece in millimeters.'))
    height_inch = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Height Inch'), help_text=_('Height of the piece in inches.'))
    length_mm = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Length MM'), help_text=_('Length of the piece in millimeters.'))
    length_inch = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Length Inch'), help_text=_('Length of the piece in inches.'))
    width_mm = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Width MM'), help_text=_('Width of the piece in millimeters.'))
    width_inch = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Width Inch'), help_text=_('Width of the piece in inches.'))
    shank_size_mm = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Shank Size MM'), help_text=_('Shank size in millimeters.'))
    shank_size_inch = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Shank Size Inch'), help_text=_('Shank size in inches.'))
    drape_length_mm = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Drape Length MM'), help_text=_('Drape length in millimeters.'))
    drape_length_inch = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name=_('Drape Length Inch'), help_text=_('Drape length in inches.'))

    design_note = models.TextField(null=True, blank=True, verbose_name=_('Design Instruction'), help_text=_('Design instructions for this piece.'))
    special_note = models.TextField(null=True, blank=True, verbose_name=_('Special Instruction'), help_text=_('Special instructions for this piece.'))
    remarks = models.TextField(null=True, blank=True, verbose_name=_('Remarks'), help_text=_('Short remarks entered on the General tab.'))

    # ---- Images tab ----
    front_view = models.ImageField(upload_to=front_view_image, null=True, blank=True, verbose_name=_('Front View'), help_text=_('Front view image of the piece.'))
    side_view = models.ImageField(upload_to=side_view_image, null=True, blank=True, verbose_name=_('Side View'), help_text=_('Side view image of the piece.'))
    back_view = models.ImageField(upload_to=back_view_image, null=True, blank=True, verbose_name=_('Back View'), help_text=_('Back view image of the piece.'))

    # ---- Labour Details tab (read-only rollups, one per source) ----
    labour_finish_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Finish Type'), help_text=_('Total labour cost rolled up from finish lines.'))
    labour_diamond_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Diamond'), help_text=_('Total labour cost rolled up from diamond lines.'))
    labour_colorstone_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Color Stone'), help_text=_('Total labour cost rolled up from color stone lines.'))

    # ---- Cost tab ----
    metal_loss_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Metal Loss %'), help_text=_('Estimated metal loss as a percentage.'))
    metal_loss_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Metal Loss Amount'), help_text=_('Computed amount lost to metal wastage.'))
    metal_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Metal Amount'), help_text=_('Computed cost of the metal used.'))

    dia_pcs = models.PositiveIntegerField(default=0, blank=True, verbose_name=_('Dia. Pcs'), help_text=_('Total diamond piece count, aggregated from diamond lines.'))
    dia_cts = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('Dia. Cts'), help_text=_('Total diamond carat weight, aggregated from diamond lines.'))
    dia_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Dia. Amount'), help_text=_('Total diamond cost, aggregated from diamond lines.'))

    col_pcs = models.PositiveIntegerField(default=0, blank=True, verbose_name=_('Col. Pcs'), help_text=_('Total color stone piece count, aggregated from color stone lines.'))
    col_cts = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('Col. Cts'), help_text=_('Total color stone carat weight, aggregated from color stone lines.'))
    col_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Col. Amount'), help_text=_('Total color stone cost, aggregated from color stone lines.'))

    stone_pcs = models.PositiveIntegerField(default=0, blank=True, verbose_name=_('Tot. Stone Pcs'), help_text=_('Combined diamond and color stone piece count.'))
    stone_cts = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('Tot. Stone Cts'), help_text=_('Combined diamond and color stone carat weight.'))
    stone_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Tot. Stone Amount'), help_text=_('Combined diamond and color stone cost.'))

    labour_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Labour Amount'), help_text=_('Total labour cost — sum of the Labour Details tab rollups.'))

    dia_handling_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Dia. Handl. Charges %'), help_text=_('Diamond handling charge as a percentage.'))
    dia_handling_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Dia. Handl. Amount'), help_text=_('Computed diamond handling charge amount.'))
    col_handling_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Col. Handl. Charges %'), help_text=_('Color stone handling charge as a percentage.'))
    col_handling_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Col. Handl. Amount'), help_text=_('Computed color stone handling charge amount.'))

    vendor_markup_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Vendor Markup %'), help_text=_('Vendor markup as a percentage.'))
    vendor_markup_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Vendor Markup Amount'), help_text=_('Computed vendor markup amount.'))

    fob = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('F.O.B'), help_text=_('Free-on-board amount for this piece.'))

    duty_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Duty %'), help_text=_('Import/export duty as a percentage.'))
    duty_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Duty Amount'), help_text=_('Computed duty amount.'))

    margin_pct = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Margin %'), help_text=_('Profit margin as a percentage.'))
    margin_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Margin Amount'), help_text=_('Computed profit margin amount.'))

    final_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Final Amount'), help_text=_('Final computed cost for this cost card.'))

    # ---- Remarks tab ----
    remarks_full = models.TextField(null=True, blank=True, verbose_name=_('Remarks (Detail)'), help_text=_('Detailed remarks entered on the dedicated Remarks tab.'))
    parent = models.ForeignKey('self', null=True, blank=True,on_delete=models.SET_NULL,related_name='child_cards',verbose_name=_('Parent Cost Card'),help_text=_('Parent cost card from which this card was copied.'),)
    
    class Meta:
        verbose_name = _('Cost Card')
        verbose_name_plural = _('Cost Cards')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['active']),
            models.Index(fields=['our_style_no']),
        ]

    def __str__(self):
        return f'{self.cost_card_no} - {self.our_style_no}'

    def save(self, *args, **kwargs):
        if not self.cost_card_no:
            last_card = CostCard.objects.order_by('-id').first()

            if last_card:
                last_number = int(last_card.cost_card_no.replace('CC', ''))
                next_number = last_number + 1
            else:
                next_number = 1

            self.cost_card_no = f'CC{next_number:06d}'

        super().save(*args, **kwargs)


class CostCardStoneLineMixin(CardsFieldsMixin):
    """Common fields shared by diamond and color stone cost card lines."""

    pointer = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name=_('Pointer'), help_text=_('Pointer value used to look up the rate.'))
    sieve_size = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Sieve Size'), help_text=_('Sieve size of the stone.'))
    pcs = models.PositiveIntegerField(default=0, verbose_name=_('Pcs'), help_text=_('Number of pieces on this line.'))
    cts = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('Cts'), help_text=_('Total carat weight on this line.'))
    default_rate = models.BooleanField(default=True, verbose_name=_('D.R.'), help_text=_('Whether the rate was pulled from the rate table (Y) or entered manually (N).'))
    pc = models.CharField(max_length=1, choices=[('P', _('Per Piece')), ('C', _('Per Carat'))], default='C', verbose_name=_('P/C'), help_text=_('Rate unit: P = Per Piece, C = Per Carat.'))
    rate = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('Rate'), help_text=_('Rate applied for this line, per piece or per carat.'))
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Amount'), help_text=_('Computed amount for this line.'))
    labour_rate = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0'), blank=True, verbose_name=_('L.Rate'), help_text=_('Labour rate applied for this line.'))
    labour_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('L.Amount'), help_text=_('Computed labour amount for this line.'))

    class Meta:
        abstract = True


class CostCardDiamondLine(CostCardStoneLineMixin):
    """Diamond tab — one row per diamond entry on a cost card."""

    cost_card = models.ForeignKey(CostCard, on_delete=models.CASCADE, related_name='diamond_lines', verbose_name=_('Cost Card'), help_text=_('Cost card this diamond line belongs to.'))
    stone = models.ForeignKey(DiamondStone, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Stone'), help_text=_('Diamond stone type.'))
    shape = models.ForeignKey(DiamondShape, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Shape'), help_text=_('Diamond shape.'))
    mm_size = models.ForeignKey(DiamondSize, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('MM Size'), help_text=_('Diamond size.'))
    color = models.ForeignKey(DiamondColor, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Color'), help_text=_('Diamond color grade.'))
    cut = models.ForeignKey(DiamondCut, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Cut'), help_text=_('Diamond cut type.'))
    quality = models.ForeignKey(DiamondQuality, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Quality'), help_text=_('Diamond quality grade.'))
    setting = models.ForeignKey(Setting, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Setting'), help_text=_('Jewelry setting used for this diamond.'))
    stone_place = models.ForeignKey(StonePlace, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Stone Place'), help_text=_('Where this diamond is placed on the piece.'))
    rate_source = models.ForeignKey(DiamondStoneRate, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_diamond_lines', verbose_name=_('Rate Source'), help_text=_('Diamond rate table row this line was originally copied from, if any.'))

    class Meta:
        verbose_name = _('Cost Card Diamond Line')
        verbose_name_plural = _('Cost Card Diamond Lines')
        ordering = ['cost_card', 'id']
        indexes = [
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f'{self.cost_card.cost_card_no} - {self.shape}'


class CostCardColorStoneLine(CostCardStoneLineMixin):
    """Color Stone tab — one row per color stone entry on a cost card."""

    cost_card = models.ForeignKey(CostCard, on_delete=models.CASCADE, related_name='colorstone_lines', verbose_name=_('Cost Card'), help_text=_('Cost card this color stone line belongs to.'))
    stone = models.ForeignKey(ColorStone, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Stone'), help_text=_('Color stone type.'))
    shape = models.ForeignKey(ColorStoneShape, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Shape'), help_text=_('Color stone shape.'))
    mm_size = models.ForeignKey(ColorStoneSize, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('MM Size'), help_text=_('Color stone size.'))
    color = models.ForeignKey(ColorStoneColor, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Color'), help_text=_('Color stone color.'))
    cut = models.ForeignKey(ColorStoneCut, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Cut'), help_text=_('Color stone cut type.'))
    quality = models.ForeignKey(ColorStoneQuality, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Quality'), help_text=_('Color stone quality grade.'))
    setting = models.ForeignKey(Setting, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Setting'), help_text=_('Jewelry setting used for this color stone.'))
    stone_place = models.ForeignKey(StonePlace, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Stone Place'), help_text=_('Where this color stone is placed on the piece.'))
    rate_source = models.ForeignKey(ColorStoneRate, null=True, blank=True, on_delete=models.SET_NULL, related_name='cost_card_colorstone_lines', verbose_name=_('Rate Source'), help_text=_('Color stone rate table row this line was originally copied from, if any.'))

    class Meta:
        verbose_name = _('Cost Card Color Stone Line')
        verbose_name_plural = _('Cost Card Color Stone Lines')
        ordering = ['cost_card', 'id']
        indexes = [
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f'{self.cost_card.cost_card_no} - {self.shape}'


class CostCardFinishLine(CardsFieldsMixin):
    """Finish Type tab — through-table for the CostCard <-> FinishType relation."""

    cost_card = models.ForeignKey(CostCard, on_delete=models.CASCADE, related_name='finish_lines', verbose_name=_('Cost Card'), help_text=_('Cost card this finish line belongs to.'))
    finish_type = models.ForeignKey(FinishType, on_delete=models.CASCADE, related_name='cost_card_finish_lines', verbose_name=_('Finish Type'), help_text=_('Finish type applied to this piece.'))
    rate = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), blank=True, verbose_name=_('Rate'), help_text=_('Rate charged for this finish.'))

    class Meta:
        verbose_name = _('Cost Card Finish Line')
        verbose_name_plural = _('Cost Card Finish Lines')
        ordering = ['cost_card', 'id']
        constraints = [
            models.UniqueConstraint(fields=['cost_card', 'finish_type'], name='unique_cost_card_finish_type'),
        ]
        indexes = [
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f'{self.cost_card.cost_card_no} - {self.finish_type}'