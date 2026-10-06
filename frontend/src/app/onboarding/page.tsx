'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
  saveStep, completeOnboarding, uploadResume,
  getCountryConfig, getProfile, ProfileData, VisaType,
} from '@/lib/api';

import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Check, Loader2, UploadCloud, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

/* ─── constants ─────────────────────────────────────────────────────────── */
const DOMAINS = [
  'Computer Science', 'Business', 'Nursing', 'Hospitality',
  'Engineering', 'Education', 'Law', 'Medicine', 'Other',
];

const EDU_LEVELS = [
  { value: 'undergraduate', label: 'Undergraduate' },
  { value: 'postgraduate',  label: 'Postgraduate / Masters' },
  { value: 'phd',           label: 'PhD / Doctoral' },
  { value: 'diploma',       label: 'Diploma / TAFE' },
  { value: 'other',         label: 'Other' },
];

const JOB_TYPE_OPTIONS = [
  { value: 'internship_domain', label: 'Internship in my domain' },
  { value: 'fulltime_domain',   label: 'Full-time job in my domain' },
  { value: 'parttime_domain',   label: 'Part-time in my domain' },
  { value: 'parttime_any',      label: 'Part-time / casual in any field' },
];

const ANY_FIELD_CATS = [
  { value: 'food_cafe',  label: 'Food & Café' },
  { value: 'retail',     label: 'Retail' },
  { value: 'delivery',   label: 'Delivery & Driving' },
  { value: 'tutoring',   label: 'Tutoring' },
  { value: 'warehouse',  label: 'Warehouse' },
  { value: 'campus',     label: 'Campus Jobs' },
];

const AVAILABILITY_OPTS = [
  { value: 'weekdays',  label: 'Weekdays' },
  { value: 'weekends',  label: 'Weekends' },
  { value: 'evenings',  label: 'Evenings' },
];

const LANG_LEVELS = [
  { value: 'none',           label: 'None' },
  { value: 'basic',          label: 'Basic' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'fluent',         label: 'Fluent / Native' },
];

const SPONSORSHIP_OPTS = [
  { value: 'yes',   label: 'Yes, I will need sponsorship' },
  { value: 'no',    label: 'No, I won\'t need it' },
  { value: 'maybe', label: 'Not sure yet' },
];

const steps = [
  { id: "profile", title: "Profile" },
  { id: "preferences", title: "Job Types" },
  { id: "location", title: "Location" },
  { id: "visa", title: "Visa" },
  { id: "language", title: "Language" },
  { id: "resume", title: "Resume" },
];

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const contentVariants = {
  hidden: { opacity: 0, x: 50 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, x: -50, transition: { duration: 0.2 } },
};

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
    </div>
  );
}

export default function OnboardingPage() {
  const { user, loading, refetch } = useAuth();
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  /* step 1 */
  const [fullName, setFullName]   = useState('');
  const [domain, setDomain]       = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [eduLevel, setEduLevel]   = useState('');
  const [gradDate, setGradDate]   = useState('');

  /* step 2 */
  const [lookingFor, setLookingFor]         = useState<string[]>([]);
  const [anyFieldCats, setAnyFieldCats]     = useState<string[]>([]);
  const [availability, setAvailability]     = useState<string[]>([]);
  const [maxHours, setMaxHours]             = useState('');

  /* step 3 */
  const [country, setCountry]   = useState('');
  const [city, setCity]         = useState('');
  const [address, setAddress]   = useState('');
  const [radius, setRadius]     = useState('10');

  /* step 4 */
  const [visaType, setVisaType]           = useState('');
  const [capTerm, setCapTerm]             = useState('');
  const [capBreak, setCapBreak]           = useState('');
  const [workRights, setWorkRights]       = useState<string>(''); // yes, no, not-sure
  const [sponsorship, setSponsorship]     = useState('');
  const [visaOptions, setVisaOptions]     = useState<VisaType[]>([]);
  const [defaultCaps, setDefaultCaps]     = useState<Record<string, [number|null, number|null]>>({});

  /* step 5 */
  const [languages, setLanguages]           = useState('');
  const [langLevel, setLangLevel]           = useState('');
  const [customerFacing, setCustomerFacing] = useState<string>(''); // yes, no

  /* step 6 */
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const [isLocating, setIsLocating] = useState(false);

  const handleLocateMe = () => {
    setIsLocating(true);
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      setIsLocating(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
          const data = await res.json();
          
          if (data && data.address) {
            if (data.address.country_code) setCountry(data.address.country_code.toUpperCase());
            const foundCity = data.address.city || data.address.town || data.address.village || data.address.county;
            if (foundCity) setCity(foundCity);
            // Optionally, we could set the address too but city/country is key
          }
        } catch (e) {
          console.error("Failed to reverse geocode:", e);
        } finally {
          setIsLocating(false);
        }
      },
      (error) => {
        console.error("Error getting location", error);
        alert("Unable to retrieve your location. Please check your browser permissions.");
        setIsLocating(false);
      }
    );
  };

  /* ── Prefill from existing profile on mount ────────────────────────────── */
  useEffect(() => {
    if (!loading && !user) router.replace('/login');
    if (user) setFullName(user.name ?? '');
  }, [user, loading, router]);

  useEffect(() => {
    getProfile().then((p: ProfileData) => {
      if (p.full_name) setFullName(p.full_name);
      if (p.domain) setDomain(DOMAINS.includes(p.domain) ? p.domain : 'Other');
      if (p.education_level) setEduLevel(p.education_level);
      if (p.grad_date) setGradDate(p.grad_date);
      if (p.looking_for) setLookingFor(p.looking_for);
      if (p.any_field_categories) setAnyFieldCats(p.any_field_categories);
      if (p.availability) setAvailability(p.availability);
      if (p.preferred_max_hours) setMaxHours(String(p.preferred_max_hours));
      if (p.country) setCountry(p.country);
      if (p.city) setCity(p.city);
      if (p.campus_address) setAddress(p.campus_address);
      if (p.commute_radius_km) setRadius(String(p.commute_radius_km));
      if (p.visa_type) setVisaType(p.visa_type);
      if (p.hour_cap_term) setCapTerm(String(p.hour_cap_term));
      if (p.hour_cap_break) setCapBreak(String(p.hour_cap_break));
      if (p.needs_sponsorship) setSponsorship(p.needs_sponsorship);
      if (p.languages) setLanguages(p.languages.join(', '));
      if (p.local_language_level) setLangLevel(p.local_language_level);
      
      if (p.comfort_customer_facing === true) setCustomerFacing("yes");
      else if (p.comfort_customer_facing === false) setCustomerFacing("no");

    }).catch(() => {});
  }, []);

  /* ── Load visa options when country changes (step 3→4) ─────────────────── */
  useEffect(() => {
    if (!country) return;
    getCountryConfig(country)
      .then(cfg => {
        setVisaOptions(cfg.visa_types);
        setDefaultCaps(cfg.default_hour_caps);
      })
      .catch(() => {});
  }, [country]);

  /* Prefill caps when visa type selected */
  useEffect(() => {
    if (!visaType || !defaultCaps[visaType]) return;
    const [term, brk] = defaultCaps[visaType];
    if (term !== null) setCapTerm(String(term));
    if (brk !== null) setCapBreak(String(brk));
  }, [visaType, defaultCaps]);

  const toggleArray = (arr: string[], val: string, setArr: (val: string[]) => void) => {
    if (arr.includes(val)) {
      setArr(arr.filter(x => x !== val));
    } else {
      setArr([...arr, val]);
    }
  };

  const handleNext = async () => {
    setError('');
    setSaving(true);
    const stepNumber = currentStep + 1;
    try {
      if (stepNumber === 1) {
        if (!fullName || !eduLevel) throw new Error('Full name and education level are required.');
        const resolvedDomain = domain === 'Other' && customDomain ? customDomain : domain;
        await saveStep(1, { full_name: fullName, domain: resolvedDomain, education_level: eduLevel, grad_date: gradDate || null });
      } else if (stepNumber === 2) {
        if (!lookingFor.length) throw new Error('Please select at least one job type.');
        if (!availability.length) throw new Error('Please select your availability.');
        await saveStep(2, {
          looking_for: lookingFor,
          any_field_categories: lookingFor.includes('parttime_any') ? anyFieldCats : [],
          availability,
          preferred_max_hours: maxHours ? Number(maxHours) : null,
        });
      } else if (stepNumber === 3) {
        if (!country || !city) throw new Error('Country and city are required.');
        await saveStep(3, {
          country: country.toUpperCase(),
          city,
          campus_address: address || null,
          commute_radius_km: Number(radius) || 10,
        });
      } else if (stepNumber === 4) {
        if (!visaType || !capTerm || !sponsorship) throw new Error('Visa type, hour cap and sponsorship are required.');
        let wr = null;
        if (workRights === 'yes') wr = true;
        if (workRights === 'no') wr = false;
        
        await saveStep(4, {
          visa_type: visaType,
          hour_cap_term: Number(capTerm),
          hour_cap_break: capBreak ? Number(capBreak) : null,
          work_rights_confirmed: wr,
          needs_sponsorship: sponsorship,
        });
      } else if (stepNumber === 5) {
        if (!langLevel) throw new Error('Please select your local language level.');
        if (!customerFacing) throw new Error('Please answer the customer-facing question.');
        await saveStep(5, {
          languages: languages ? languages.split(',').map(s => s.trim()).filter(Boolean) : [],
          local_language_level: langLevel,
          comfort_customer_facing: customerFacing === 'yes',
        });
      } else if (stepNumber === 6) {
        if (resumeFile) {
          const res = await uploadResume(resumeFile);
          if (!res.ok) throw new Error('Resume upload failed.');
        }
        await completeOnboarding();
        await refetch();
        router.replace('/jobs');
        return;
      }
      setCurrentStep(s => s + 1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong.');
    } finally {
      setSaving(false);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return fullName.trim() !== '' && domain !== '' && eduLevel !== '';
      case 1:
        return lookingFor.length > 0 && availability.length > 0;
      case 2:
        return country.trim() !== '' && city.trim() !== '';
      case 3:
        return visaType !== '' && capTerm !== '' && sponsorship !== '';
      case 4:
        return langLevel !== '' && customerFacing !== '';
      default:
        return true;
    }
  };

  if (loading) return <LoadingScreen />;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col pt-12 pb-24 px-4 overflow-y-auto">
      <div className="w-full max-w-2xl mx-auto">
        <div className="flex flex-col items-center gap-2 mb-10">
          <div className="bg-blue-600 p-2.5 rounded-xl text-white shadow-sm mb-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
            </svg>
          </div>
          <span className="text-2xl font-bold tracking-tight text-slate-900">Complete your profile</span>
        </div>

        {/* Progress indicator */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex justify-between mb-2">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                className="flex flex-col items-center"
              >
                <motion.div
                  className={cn(
                    "flex items-center justify-center w-7 h-7 rounded-full cursor-pointer transition-colors duration-300 text-xs font-semibold select-none",
                    index < currentStep
                      ? "bg-blue-600 text-white"
                      : index === currentStep
                        ? "bg-blue-600 ring-4 ring-blue-600/20 text-white"
                        : "bg-slate-200 text-slate-500",
                  )}
                  onClick={() => {
                    if (index <= currentStep) setCurrentStep(index);
                  }}
                  whileTap={{ scale: 0.95 }}
                >
                  {index < currentStep ? <Check className="w-4 h-4" strokeWidth={3} /> : index + 1}
                </motion.div>
                <motion.span
                  className={cn(
                    "text-xs mt-2 hidden sm:block font-medium tracking-wide",
                    index === currentStep
                      ? "text-blue-600"
                      : "text-slate-400",
                  )}
                >
                  {step.title}
                </motion.span>
              </motion.div>
            ))}
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-2">
            <motion.div
              className="h-full bg-blue-600"
              initial={{ width: 0 }}
              animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </motion.div>

        {/* Form card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Card className="border shadow-md rounded-3xl overflow-hidden bg-white">
            <div>
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  variants={contentVariants}
                >
                  
                  {/* Step 1: Personal Info */}
                  {currentStep === 0 && (
                    <>
                      <CardHeader>
                        <CardTitle>Tell us about yourself</CardTitle>
                        <CardDescription>
                          Let's start with some basic information.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="name">Full Name <span className="text-red-500">*</span></Label>
                          <Input
                            id="name"
                            placeholder="Jane Smith"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
                          />
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="domain">Field of Study <span className="text-red-500">*</span></Label>
                          <Select value={domain} onValueChange={setDomain}>
                            <SelectTrigger id="domain" className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">
                              <SelectValue placeholder="Select a field" />
                            </SelectTrigger>
                            <SelectContent>
                              {DOMAINS.map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </motion.div>
                        {domain === 'Other' && (
                          <motion.div variants={fadeInUp} className="space-y-2">
                            <Label htmlFor="customDomain">Specify your field</Label>
                            <Input
                              id="customDomain"
                              placeholder="e.g. Architecture"
                              value={customDomain}
                              onChange={(e) => setCustomDomain(e.target.value)}
                              className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
                            />
                          </motion.div>
                        )}
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="eduLevel">Education Level <span className="text-red-500">*</span></Label>
                          <Select value={eduLevel} onValueChange={setEduLevel}>
                            <SelectTrigger id="eduLevel" className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">
                              <SelectValue placeholder="Select level" />
                            </SelectTrigger>
                            <SelectContent>
                              {EDU_LEVELS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="gradDate">Expected Graduation Date</Label>
                          <Input
                            id="gradDate"
                            type="month"
                            value={gradDate}
                            onChange={(e) => setGradDate(e.target.value)}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 w-full flex h-10"
                          />
                        </motion.div>
                      </CardContent>
                    </>
                  )}

                  {/* Step 2: Job Types */}
                  {currentStep === 1 && (
                    <>
                      <CardHeader>
                        <CardTitle>What are you looking for?</CardTitle>
                        <CardDescription>Select the types of opportunities you are interested in.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        <motion.div variants={fadeInUp} className="space-y-3">
                          <Label>Select all that apply</Label>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {JOB_TYPE_OPTIONS.map((opt) => (
                              <motion.div
                                key={opt.value}
                                className={cn("flex items-center space-x-2 rounded-md border p-3 cursor-pointer transition-colors", lookingFor.includes(opt.value) ? "border-blue-600 bg-blue-50" : "hover:bg-slate-50")}
                                onClick={() => toggleArray(lookingFor, opt.value, setLookingFor)}
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                <Checkbox checked={lookingFor.includes(opt.value)} onCheckedChange={() => toggleArray(lookingFor, opt.value, setLookingFor)} />
                                <Label className="cursor-pointer w-full font-normal">{opt.label}</Label>
                              </motion.div>
                            ))}
                          </div>
                        </motion.div>

                        {lookingFor.includes('parttime_any') && (
                          <motion.div variants={fadeInUp} className="space-y-3 pt-2">
                            <Label>Preferred casual categories</Label>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {ANY_FIELD_CATS.map((opt) => (
                                <motion.div
                                  key={opt.value}
                                  className={cn("flex items-center space-x-2 rounded-md border p-3 cursor-pointer transition-colors", anyFieldCats.includes(opt.value) ? "border-blue-600 bg-blue-50" : "hover:bg-slate-50")}
                                  onClick={() => toggleArray(anyFieldCats, opt.value, setAnyFieldCats)}
                                  whileHover={{ scale: 1.01 }}
                                  whileTap={{ scale: 0.98 }}
                                >
                                  <Checkbox checked={anyFieldCats.includes(opt.value)} onCheckedChange={() => toggleArray(anyFieldCats, opt.value, setAnyFieldCats)} />
                                  <Label className="cursor-pointer w-full font-normal">{opt.label}</Label>
                                </motion.div>
                              ))}
                            </div>
                          </motion.div>
                        )}

                        <motion.div variants={fadeInUp} className="space-y-3 pt-2">
                          <Label>Availability</Label>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {AVAILABILITY_OPTS.map((opt) => (
                              <motion.div
                                key={opt.value}
                                className={cn("flex items-center space-x-2 rounded-md border p-3 cursor-pointer transition-colors", availability.includes(opt.value) ? "border-blue-600 bg-blue-50" : "hover:bg-slate-50")}
                                onClick={() => toggleArray(availability, opt.value, setAvailability)}
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                <Checkbox checked={availability.includes(opt.value)} onCheckedChange={() => toggleArray(availability, opt.value, setAvailability)} />
                                <Label className="cursor-pointer w-full font-normal">{opt.label}</Label>
                              </motion.div>
                            ))}
                          </div>
                        </motion.div>

                        <motion.div variants={fadeInUp} className="space-y-2 pt-2">
                          <Label htmlFor="maxHours">Preferred max hours per week</Label>
                          <Input
                            id="maxHours"
                            type="number"
                            placeholder="e.g. 20"
                            value={maxHours}
                            onChange={(e) => setMaxHours(e.target.value)}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
                          />
                        </motion.div>
                      </CardContent>
                    </>
                  )}

                  {/* Step 3: Location */}
                  {currentStep === 2 && (
                    <>
                      <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                          <CardTitle>Where are you based?</CardTitle>
                          <CardDescription>This helps us find opportunities near you.</CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleLocateMe}
                          disabled={isLocating}
                          className="flex items-center gap-2"
                        >
                          {isLocating ? <Loader2 className="w-4 h-4 animate-spin" /> : <MapPin className="w-4 h-4" />}
                          Use my location
                        </Button>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="country">Country code <span className="text-red-500">*</span></Label>
                          <Input
                            id="country"
                            placeholder="e.g. AU, US, GB"
                            value={country}
                            onChange={(e) => setCountry(e.target.value.toUpperCase())}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 uppercase"
                          />
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="city">City <span className="text-red-500">*</span></Label>
                          <Input
                            id="city"
                            placeholder="e.g. Melbourne"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
                          />
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label htmlFor="address">Campus or home address (optional)</Label>
                          <Input
                            id="address"
                            placeholder="123 University Ave"
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
                          />
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2 pt-2">
                          <div className="flex justify-between">
                            <Label>Max commute radius</Label>
                            <span className="text-sm font-semibold text-blue-600">{radius} km</span>
                          </div>
                          <input
                            type="range" min={1} max={100} value={radius}
                            onChange={e => setRadius(e.target.value)}
                            className="w-full accent-blue-600 mt-2"
                          />
                        </motion.div>
                      </CardContent>
                    </>
                  )}

                  {/* Step 4: Visa */}
                  {currentStep === 3 && (
                    <>
                      <CardHeader>
                        <CardTitle>Visa & Work Rights</CardTitle>
                        <CardDescription>Information required for compliance and sponsorship.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label>Visa type <span className="text-red-500">*</span></Label>
                          {visaOptions.length > 0 ? (
                            <Select value={visaType} onValueChange={setVisaType}>
                              <SelectTrigger className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">
                                <SelectValue placeholder="Select visa type" />
                              </SelectTrigger>
                              <SelectContent>
                                {visaOptions.map(v => <SelectItem key={v.code} value={v.code}>{v.label}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          ) : (
                            <Input
                              placeholder="Enter your visa type"
                              value={visaType}
                              onChange={(e) => setVisaType(e.target.value)}
                            />
                          )}
                        </motion.div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <motion.div variants={fadeInUp} className="space-y-2">
                            <Label>Hour cap (term, /wk) <span className="text-red-500">*</span></Label>
                            <Input
                              type="number"
                              placeholder="e.g. 20"
                              value={capTerm}
                              onChange={(e) => setCapTerm(e.target.value)}
                            />
                          </motion.div>
                          <motion.div variants={fadeInUp} className="space-y-2">
                            <Label>Hour cap (break, /wk)</Label>
                            <Input
                              type="number"
                              placeholder="Unlimited?"
                              value={capBreak}
                              onChange={(e) => setCapBreak(e.target.value)}
                            />
                          </motion.div>
                        </div>

                        <motion.div variants={fadeInUp} className="space-y-3">
                          <Label>Is your work-rights condition stored on your visa?</Label>
                          <RadioGroup value={workRights} onValueChange={setWorkRights} className="flex gap-6">
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="yes" id="wr-yes" />
                              <Label htmlFor="wr-yes" className="font-normal cursor-pointer">Yes</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="no" id="wr-no" />
                              <Label htmlFor="wr-no" className="font-normal cursor-pointer">No</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="not-sure" id="wr-maybe" />
                              <Label htmlFor="wr-maybe" className="font-normal cursor-pointer">Not sure</Label>
                            </div>
                          </RadioGroup>
                        </motion.div>

                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label>Will you need visa sponsorship after graduation? <span className="text-red-500">*</span></Label>
                          <Select value={sponsorship} onValueChange={setSponsorship}>
                            <SelectTrigger className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">
                              <SelectValue placeholder="Select" />
                            </SelectTrigger>
                            <SelectContent>
                              {SPONSORSHIP_OPTS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </motion.div>

                        <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 leading-relaxed">
                          Always confirm your work-hour limits with your university or official immigration source.
                        </p>
                      </CardContent>
                    </>
                  )}

                  {/* Step 5: Language */}
                  {currentStep === 4 && (
                    <>
                      <CardHeader>
                        <CardTitle>Language & Comfort</CardTitle>
                        <CardDescription>Details about your communication skills.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label>Languages spoken (comma-separated)</Label>
                          <Input
                            placeholder="e.g. English, Mandarin, Hindi"
                            value={languages}
                            onChange={(e) => setLanguages(e.target.value)}
                          />
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label>Local language level <span className="text-red-500">*</span></Label>
                          <Select value={langLevel} onValueChange={setLangLevel}>
                            <SelectTrigger className="transition-all duration-300 focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">
                              <SelectValue placeholder="Select proficiency" />
                            </SelectTrigger>
                            <SelectContent>
                              {LANG_LEVELS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </motion.div>
                        <motion.div variants={fadeInUp} className="space-y-3">
                          <Label>Comfortable with customer-facing roles? <span className="text-red-500">*</span></Label>
                          <RadioGroup value={customerFacing} onValueChange={setCustomerFacing} className="flex gap-6">
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="yes" id="cf-yes" />
                              <Label htmlFor="cf-yes" className="font-normal cursor-pointer">Yes</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="no" id="cf-no" />
                              <Label htmlFor="cf-no" className="font-normal cursor-pointer">No</Label>
                            </div>
                          </RadioGroup>
                        </motion.div>
                      </CardContent>
                    </>
                  )}

                  {/* Step 6: Resume */}
                  {currentStep === 5 && (
                    <>
                      <CardHeader>
                        <CardTitle>Resume & Notifications</CardTitle>
                        <CardDescription>Final steps before you can start applying.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <motion.div variants={fadeInUp} className="space-y-2">
                          <Label>Upload resume (PDF, max 5 MB) <span className="text-slate-500 font-normal">- optional</span></Label>
                          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl p-8 cursor-pointer hover:border-blue-500 hover:bg-blue-50/50 transition bg-slate-50/50">
                            <UploadCloud className="w-8 h-8 text-slate-400" />
                            <span className="text-sm text-slate-600 font-medium">{resumeFile ? resumeFile.name : 'Click to upload PDF'}</span>
                            <input type="file" accept="application/pdf" className="hidden" onChange={e => setResumeFile(e.target.files?.[0] ?? null)} />
                          </label>
                        </motion.div>

                        <motion.div variants={fadeInUp} className="bg-blue-50 border border-blue-100 rounded-xl p-5 flex flex-col gap-1.5">
                          <p className="text-sm font-semibold text-blue-900">Connect Telegram (optional)</p>
                          <p className="text-xs text-blue-700">After finishing, go to Settings → Connect Telegram to get job alerts.</p>
                        </motion.div>

                        <p className="text-sm text-slate-500 text-center">You can skip both and set them up later in Settings.</p>
                      </CardContent>
                    </>
                  )}
                  
                  {error && (
                    <div className="px-6 pb-2">
                      <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 font-medium">{error}</p>
                    </div>
                  )}

                </motion.div>
              </AnimatePresence>

              <CardFooter className="flex justify-between pt-6 pb-6 bg-slate-50/50 border-t">
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={prevStep}
                    disabled={currentStep === 0 || saving}
                    className="flex items-center gap-1 transition-all duration-300 rounded-full px-6 shadow-sm bg-white"
                  >
                    <ChevronLeft className="h-4 w-4" /> Back
                  </Button>
                </motion.div>
                
                <motion.div whileHover={!(!isStepValid() || saving) ? { scale: 1.02 } : {}} whileTap={!(!isStepValid() || saving) ? { scale: 0.98 } : {}}>
                  <Button
                    type="button"
                    onClick={handleNext}
                    disabled={!isStepValid() || saving}
                    className="flex items-center gap-1 transition-all duration-300 rounded-full px-8 shadow-sm bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Saving...
                      </>
                    ) : (
                      <>
                        {currentStep === steps.length - 1 ? "Finish & Find Jobs" : "Next"}
                        {currentStep === steps.length - 1 ? (
                          <Check className="h-4 w-4 ml-1" />
                        ) : (
                          <ChevronRight className="h-4 w-4 ml-1" />
                        )}
                      </>
                    )}
                  </Button>
                </motion.div>
              </CardFooter>
            </div>
          </Card>
        </motion.div>

        {/* Step indicator text */}
        <motion.div
          className="mt-6 text-center text-sm text-slate-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
        </motion.div>
      </div>
    </div>
  );
}
