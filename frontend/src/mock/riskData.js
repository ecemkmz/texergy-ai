export const mockRisks = [
  {
    id: 'r1',
    category: 'Enerji',
    title: 'Boyahane Buhar Kazanı - Verimlilik Düşüşü',
    score: 82,
    severity: 'high',
    description:
      'Kazan çıkış basıncı son 72 saatte kademeli düşüş gösteriyor, bu da yakıt tüketiminde beklenenin üzerinde artışa işaret ediyor.',
    action: 'Kazan bakım ekibini 24 saat içinde yönlendirin, izolasyon kayıplarını kontrol edin.',
  },
  {
    id: 'r2',
    category: 'Üretim',
    title: 'Dokuma Salonu 3 - Duruş Süresi Artışı',
    score: 64,
    severity: 'medium',
    description:
      'Planlanmamış duruş süresi geçen haftaya göre %18 arttı, tekrarlayan hata kodu aynı tezgahtan geliyor.',
    action: 'İlgili tezgahın bakım geçmişini inceleyin, tekrarlayan arıza kalıbı var mı doğrulayın.',
  },
  {
    id: 'r3',
    category: 'Kalite',
    title: 'Apre Hattı - Renk Sapması',
    score: 45,
    severity: 'medium',
    description:
      'Son 3 partide ölçülen renk farkı (Delta E) tolerans sınırına yaklaşıyor ancak henüz aşmadı.',
    action: 'Bir sonraki partide numune sıklığını artırın, reçete parametrelerini gözden geçirin.',
  },
  {
    id: 'r4',
    category: 'Bakım',
    title: 'Kompresör Ünitesi 2 - Titreşim Anomalisi',
    score: 71,
    severity: 'high',
    description:
      'Titreşim sensörü referans aralığın üzerinde okuma yapıyor, rulman aşınmasına işaret edebilir.',
    action: 'Önleyici bakımı planlayın; beklenmeyen duruş riski üretim programını etkileyebilir.',
  },
  {
    id: 'r5',
    category: 'Enerji',
    title: 'Kurutma Fırını - Vardiya Dışı Tüketim',
    score: 38,
    severity: 'low',
    description:
      'Gece vardiyasında fırının bekleme modunda beklenenden fazla enerji tükettiği görülüyor.',
    action: 'Bekleme modu eşiklerini gözden geçirin, otomatik kapanma süresini kısaltmayı değerlendirin.',
  },
  {
    id: 'r6',
    category: 'Üretim',
    title: 'İplik Büküm Hattı - Verim Kaybı',
    score: 22,
    severity: 'low',
    description:
      'Genel verim son bir haftadır hedefin hafif altında seyrediyor, tek bir kök neden henüz belirgin değil.',
    action: 'İzlemeye devam edin; trend 1 haftadan uzun sürerse kök neden analizi başlatın.',
  },
]
export const categories = ['Tümü', 'Enerji', 'Üretim', 'Kalite', 'Bakım']