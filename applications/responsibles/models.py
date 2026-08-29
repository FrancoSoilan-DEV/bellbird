# applications/auctions/models.py
from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models

from .managers import AuctionQuerySet
from .mixins import TimestampedModel


class Auction(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        ACTIVE = 'active', 'Active'
        SOLD = 'sold', 'Sold'
        UNSOLD = 'unsold', 'Unsold'
        CANCELLED = 'cancelled', 'Cancelled'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auctions',
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auctions_won',
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attributes = models.JSONField(default=dict, blank=True)

    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    buy_now_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    objects = AuctionQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['status', 'ends_at']),
            GinIndex(fields=['attributes']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(starting_price__gte=0),
                name='auction_starting_price_non_negative',
            ),
            models.CheckConstraint(
                check=models.Q(ends_at__gt=models.F('starts_at')),
                name='auction_ends_after_starts',
            ),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding and self.current_price is None:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)

    def clean(self):
        if self.reserve_price is not None and self.reserve_price < self.starting_price:
            raise ValidationError('reserve_price no puede ser menor a starting_price.')

    def __str__(self):
        return self.title


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['auction', '-amount']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='bid_amount_positive'),
        ]

    def clean(self):
        if self.bidder_id == self.auction.seller_id:
            raise ValidationError('El vendedor no puede pujar en su propia subasta.')

    def __str__(self):
        return f'{self.bidder} → {self.auction} (${self.amount})'